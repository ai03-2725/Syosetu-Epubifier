import { createEffect, createMemo, createSignal, ErrorBoundary, For, Suspense } from 'solid-js'
import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from '@tanstack/solid-query'

import '@globus.studio/oat-table/dist/oat-table.min.css';
import '@globus.studio/oat-table/dist/oat-table.min.js';
import { BACKEND_IP } from '..';
import type { Novel } from '../types/novel';
import type { EpubFile } from '../types/epub-file';

import IconBook from '~icons/ph/book-open'
import IconDownload from '~icons/ph/download'
import IconWrench from '~icons/ph/wrench'
import IconLink from '~icons/ph/link'
import IconCopy from '~icons/ph/copy'
import { awaitEpubGen } from '../queries/AwaitEpubGen';
import { deleteNovel, getAllNovels, toggleNovelFrozenState } from '../queries/Novel';
import { getAllEpubFiles } from '../queries/EpubFile';
import { enqueueNovelUpdateTask, getAllUpdateNovelJobs, type GetAllUpdateNovelJobsReturnType } from '../queries/UpdateNovelJobs';
import type { RqJobStatus } from '../types/rq-job-statuses';
import { getJobStatus } from '../queries/GetJobStatus';


function NovelsPage() {
  const [selectedRows, setSelectedRows] = createSignal<number[]>([])
  const [visibleRows, setVisibleRows] = createSignal<number>(0)
  const [currentlyPendingNovel, setCurrentlyPendingNovel] = createSignal<Novel | null>(null)
  const queryClient = useQueryClient()

  createEffect(() => {
    console.log(`Selected rows: ${selectedRows()}`);
    console.log(`Visible rows: ${visibleRows()}`)
  })


  // =====
  // Queries
  // =====

  const novelsQuery = useQuery<Novel[]>(() => ({
    queryKey: ['novels'],
    queryFn: getAllNovels,
    throwOnError: true, // Throw an error if the query fails
  }))

  const epubFilesQuery = useQuery<EpubFile[]>(() => ({
    queryKey: ['epub-files'],
    queryFn: getAllEpubFiles,
    throwOnError: true, // Throw an error if the query fails
  }))

  const updateJobsQuery = useQuery<GetAllUpdateNovelJobsReturnType[]>(() => ({
    queryKey: ['novel-update-jobs'],
    queryFn: getAllUpdateNovelJobs,
    refetchInterval: 10 * 1000, // 10s
    throwOnError: true, // Throw an error if the query fails
  }))

  // Create dependent array from updateJobsQuery to build a guaranteed existent jobs array
  const updateJobs = createMemo<GetAllUpdateNovelJobsReturnType[]>(() => {
    return updateJobsQuery.data || []
  })

  // Use above to run parallel queries on job logs with variable refetch interval for logs
  const jobStatuses = useQueries(() => ({
    queries: updateJobs().map(job => ({
      queryKey: ['job-status', job.jobId],
      queryFn: () => getJobStatus(job.jobId),
      refetchInterval: (query: any) => {
        const currentStatus: RqJobStatus = query.state.data?.status
        switch (currentStatus) {
          case "queued":
          case "created":
          case "deferred":
            return 4 * 1000 // For pending jobs, refetch once every 4 seconds
          case "started":
            return 1 * 1000 // For active jobs, refetch once every 1 second
          default:
            // Otherwise don't refetch
            return false
        }
      }
    })),
  }))


  // =====
  // Mutations
  // =====

  const deleteNovelMutation = useMutation(() => ({
    mutationFn: async (novelId: number) => {await deleteNovel(novelId)},
    onError: (e) => {
      (window as any).ot.toast(e.message, '削除に失敗しました', { variant: 'warning', placement: 'bottom-right', duration: 10 * 1000 });
      console.error(e)
    },
    onSuccess: () => {
      // Invalidate the cache to trigger refetching
      queryClient.invalidateQueries({ queryKey: ['novels'] });
      setCurrentlyPendingNovel(null);
      (window as any).ot.toast(`小説は削除されました`, '削除成功', { variant: 'success', placement: 'bottom-right', duration: 5 * 1000 })
    },
    onSettled: () => {
      const deleteDialog = document.getElementById("delete-dialog") as HTMLDialogElement;
      deleteDialog.close()
    }
  }))

  const generateEpubMutation = useMutation(() => ({
    mutationFn: async (novelId: number) => {await awaitEpubGen(novelId)},
    onError: (e) => {
      (window as any).ot.toast(e.message, 'ePub出力に失敗しました', { variant: 'warning', placement: 'bottom-right', duration: 10 * 1000 });
      console.error(e)
    },
    onSuccess: () => {
      // Invalidate the cache to trigger refetching
      queryClient.invalidateQueries({ queryKey: ['novels'] });
      setCurrentlyPendingNovel(null);
      (window as any).ot.toast(`ePubファイルが出力されました`, '出力成功', { variant: 'success', placement: 'bottom-right', duration: 5 * 1000 })
      const epubPopovers = document.querySelectorAll<HTMLMenuElement>('[id*="epub-actions-"]');
      epubPopovers.forEach(popover => popover.hidePopover())
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['epub-files'] });
    }
  }))

  const enqueueNovelFetchMutation = useMutation(() => ({
    mutationFn: async (novelIds: number[] | true) => {await enqueueNovelUpdateTask(novelIds)},
    onError: (e) => {
      (window as any).ot.toast(e.message, '更新に失敗しました', { variant: 'warning', placement: 'bottom-right', duration: 10 * 1000 });
      console.error(e)
    },
    onSuccess: () => {
      (window as any).ot.toast(`小説の更新を開始しました`, '更新開始', { variant: 'success', placement: 'bottom-right', duration: 5 * 1000 })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['novel-update-jobs'] });
    }
  }))

  const toggleNovelFrozenStateMutation = useMutation(() => ({
    mutationFn: async (novel: Novel) => {await toggleNovelFrozenState(novel)},
    onError: (e) => {
      (window as any).ot.toast(e.message, '更新に失敗しました', { variant: 'warning', placement: 'bottom-right', duration: 10 * 1000 });
      console.error(e)
    },
    onSuccess: () => {
      (window as any).ot.toast(`小説の更新を開始しました`, '更新開始', { variant: 'success', placement: 'bottom-right', duration: 5 * 1000 })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['novels'] });
      const freezeDialog = document.getElementById("freeze-dialog") as HTMLDialogElement;
      freezeDialog.close()
    }
  }))


  // =====
  // Helpers
  // =====

  const isNovelUpdating = (novelId: number) => {
    // First get corresponding job ID from the running update jobs list...
    const jobId = updateJobsQuery.data?.find(entry => entry.novelId === novelId)?.jobId
    if (!jobId) return false
    // ...then get its current state
    const correspondingJob = jobStatuses.find(job => job.data?.jobId === jobId)?.data
    if (!correspondingJob) return false
    return ["queued", "created", "started", "deferred"].includes(correspondingJob.status)
  }

  const copySourceUrlToClipboard = async (url: string) => {
    await navigator.clipboard.writeText(url);
    (window as any).ot.toast(`小説のURL「${url}」をコピーしました`, 'URLをコピーしました', { variant: 'success', placement: 'bottom-right', duration: 5 * 1000 })
  }


  return (
    <div id="novels-table-wrapper">
      <ErrorBoundary fallback={<div>エラーが発生しました</div>}>
        <Suspense fallback={<div style="width: 100%; height: 100%;" data-spinner="overlay"></div>}>
          <output data-table-selected aria-live="polite"></output>
          <ot-table 
            empty-text='該当する小説はありません'
            on:ot-table-select={(e: any) => setSelectedRows(e.detail.selectedValues.map((value: any) => Number(value)))}
            on:ot-table-filter={(e: any) => setVisibleRows(e.detail.visibleRows.length)}
          >
            <div class="hstack gap-2 mb-4">
              <form data-table-toolbar role="search">
                <input id="form-search" type="search" data-table-filter placeholder="検索" style="margin-top: 0;" />
              </form>
              <div class="vstack" style="height: 100%;">
                <button 
                  disabled={selectedRows().length <= 0}
                  onClick={() => enqueueNovelFetchMutation.mutate(selectedRows())}
                >選択された小説を更新</button>
              </div>
              <div class="vstack" style="height: 100%;">
                <button 
                  disabled={(novelsQuery.data?.length || 0) <= 0}
                  onClick={() => enqueueNovelFetchMutation.mutate(true)}
                >全ての小説を更新</button>
              </div>
            </div>

            <div class="table">
              <table>
                <thead>
                  <tr>
                    <th scope="col"><input type="checkbox" data-table-select-all aria-label="全ての小説を選択" /></th>
                    <th scope="col" data-sort>タイトル</th>
                    <th scope="col" data-sort>作者</th>
                    <th scope="col" data-sort>URL</th>
                    <th scope="col">タグ</th>
                    <th scope="col" data-sort="date">取得日</th>
                    <th scope="col" data-sort="date">更新日</th>
                    <th scope="col">更新</th>
                    <th scope="col">管理</th>
                    <th scope="col">ePub</th>
                  </tr>
                </thead>

                <tbody>
                  <For each={novelsQuery.data}>
                  {((novel) => (
                    <tr data-filter-text={`${novel.title} ${novel.author} ${novel.source} ${novel.tags.join(" ")}`}>
                      <td><input type="checkbox" data-table-select-row value={novel.id} aria-label={`「${novel.title}」を選択`} /></td>
                      <td data-sort-value={novel.title} style="max-width: 250px;">{novel.title}</td>
                      <td data-sort-value={novel.author} style="max-width: 200px;">{novel.author}</td>
                      <td data-sort-value={novel.source}>
                          <menu class="buttons">
                          <li style="margin-bottom: 0px;"><button class="outline" onClick={() => window.open(novel.source, '_blank')}><IconLink style="vertical-align: middle" /></button></li>
                          <li style="margin-bottom: 0px;"><button class="outline" onClick={() => copySourceUrlToClipboard(novel.source)}><IconCopy style="vertical-align: middle" /></button></li>
                        </menu>
                        
                      </td>
                      <td style="max-width: 250px;">
                        {novel.frozen && <><span class="badge" data-variant="warning">凍結中</span></>}
                        <For each={novel.tags}>
                          {((tag) => (
                            <span class="badge" data-variant="secondary">{tag}</span>
                          ))}
                        </For>
                      </td>
                      <td><time datetime={novel.lastFetchTimestamp.toISOString()}>{novel.lastFetchTimestamp.toLocaleDateString()}<br/>{novel.lastFetchTimestamp.toLocaleTimeString()}</time></td>
                      <td><time datetime={novel.lastUpdatedTimestamp.toISOString()}>{novel.lastUpdatedTimestamp.toLocaleDateString()}<br/>{novel.lastUpdatedTimestamp.toLocaleTimeString()}</time></td>
                      <td>
                        {/* Update button stack */}
                        <ot-dropdown>
                          <menu class="buttons">
                            <li style="margin-bottom: 0px;">
                              <button 
                                class="outline"
                                aria-busy={isNovelUpdating(novel.id)} 
                                data-spinner="small"
                                disabled={novel.frozen || isNovelUpdating(novel.id) || enqueueNovelFetchMutation.isPending} 
                                onClick={() => enqueueNovelFetchMutation.mutate([novel.id])}
                              ><IconDownload /></button>
                            </li>
                            <li style="margin-bottom: 0px;">
                              <button  class="outline" popovertarget="save-actions" aria-label="その他の更新モード" style="height: 100%;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6" /></svg>
                              </button>
                            </li>
                          </menu>
                          <menu popover id="save-actions">
                            <button role="menuitem" class="ghost" data-variant="danger" disabled>削除モードで更新</button>
                          </menu>
                        </ot-dropdown>
                      </td>
                      <td>
                        {/* Manage button stack */}
                        <ot-dropdown>
                          <button  class="outline" popovertarget={`other-actions-${novel.id}`} aria-label="その他">
                            <IconWrench />
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6" /></svg>
                          </button>
                          <menu popover id={`other-actions-${novel.id}`}>
                            <button role="menuitem" class="ghost" disabled>バックアップを作製</button>
                            <button role="menuitem" class="ghost" commandfor="freeze-dialog" command="show-modal" onClick={[setCurrentlyPendingNovel, novel]}>小説{novel.frozen ? "の凍結を解除" : "を凍結"}</button>
                            <button role="menuitem" class="ghost" commandfor="delete-dialog" command="show-modal" onClick={[setCurrentlyPendingNovel, novel]} data-variant="danger">小説を削除</button>
                          </menu>
                        </ot-dropdown>
                      </td>
                      <td>
                        {/* Epub button stack */}
                        <ot-dropdown>
                          <button  class="outline" popovertarget={`epub-actions-${novel.id}`} aria-label="その他">
                            <IconBook />
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6" /></svg>
                          </button>
                          <menu popover id={`epub-actions-${novel.id}`}>
                            <button role="menuitem" class="ghost" data-spinner="small"
                              onClick={() => generateEpubMutation.mutate(novel.id)} 
                              aria-busy={generateEpubMutation.isPending} disabled={generateEpubMutation.isPending}
                            >ePubファイルを{epubFilesQuery.data?.find(entry => entry.novel == novel.id) ? "際" : undefined}生成</button>
                            {epubFilesQuery.data?.find(entry => entry.novel == novel.id) && 
                             <button role="menuitem" class="ghost"
                              onclick={() => window.open(BACKEND_IP + `/novel/epub-files/${novel.id}`, '_blank')}
                              popovertarget={`epub-actions-${novel.id}`}
                              popovertargetaction='hide'
                            >ダウンロード</button>
                            }
                          </menu>
                        </ot-dropdown>
                      </td>
                    </tr>
                  ))}
                  </For>

                </tbody>

              </table>
            </div>
          </ot-table>
        </Suspense>
      </ErrorBoundary>
      <dialog id="freeze-dialog" closedby={toggleNovelFrozenStateMutation.isPending ? "none" : "any"}>
        <form method="dialog">
          <header>
            <h3>小説の凍結</h3>
          </header>
          <div>
            <p>小説「{currentlyPendingNovel()?.title}」{currentlyPendingNovel()?.frozen ? "の凍結を解除" : "を凍結"}しますか？</p>
            {currentlyPendingNovel()?.frozen ? 
                <p>凍結を解除された小説は更新できるようになります。<br/>
                また、自動更新も再開されます。</p>
                :
                <p>凍結された小説は更新できなくなります。<br/>
                また、自動更新も行われなくなります。</p>
            }
          </div>
          <footer>
            <button type="button" commandfor="freeze-dialog" command="close" class="outline" disabled={toggleNovelFrozenStateMutation.isPending}>キャンセル</button>
            <button value="confirm" 
              onClick={() => toggleNovelFrozenStateMutation.mutate(currentlyPendingNovel()!)}
              disabled={toggleNovelFrozenStateMutation.isPending}
            >{currentlyPendingNovel()?.frozen ? "凍結を解除" : "凍結"}</button>
          </footer>
        </form>
      </dialog>

      <dialog id="delete-dialog" closedby={deleteNovelMutation.isPending ? "none" : "any"}>
        <form method="dialog">
          <header>
            <h3>小説の削除</h3>
          </header>
          <div>
            <p>小説「{currentlyPendingNovel() ? currentlyPendingNovel()?.title : ""}」を削除しますか？</p>
            <p>データは復元できません。</p>
          </div>
          <footer>
            <button type="button" commandfor="freeze-dialog" command="close" class="outline" disabled={deleteNovelMutation.isPending}>キャンセル</button>
            {/* <button type="button" commandfor="freeze-dialog" command="close" class="outline" disabled={deleteNovelMutation.isPending}>バックアップを取得</button> */}
            <button value="confirm" data-variant="danger" data-spinner="small"
              onClick={() => deleteNovelMutation.mutate(currentlyPendingNovel()?.id)} 
              disabled={deleteNovelMutation.isPending} 
              aria-busy={deleteNovelMutation.isPending}>削除</button>
          </footer>
        </form>
      </dialog>

    </div>
  )
}

export default NovelsPage
