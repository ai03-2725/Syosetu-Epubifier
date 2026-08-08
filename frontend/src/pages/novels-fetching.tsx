import { createEffect, createMemo, createSignal, ErrorBoundary, For, Suspense } from 'solid-js'
import {
  useQueries,
  useQuery,
} from '@tanstack/solid-query'

import '@globus.studio/oat-table/dist/oat-table.min.css';
import '@globus.studio/oat-table/dist/oat-table.min.js';
import { AddFetchNovelSection } from '../component/AddFetchNovelSection';
import IconNotebook from '~icons/ph/notebook'
import type { RqJobStatus, JobStatusReturnType } from '../types/rq-job-statuses';
import { getJobStatus } from '../queries/GetJobStatus';
import { getAllFetchNovelJobs, type GetAllFetchNovelJobsReturnType } from '../queries/FetchNovelJobs';
import { RqJobStatusBadge } from '../component/RqJobStatusBadge';


function NovelsFetchingPage() {

  const [displayedJobId, setDisplayedJobId] = createSignal<string>("")
  const [displayedLog, setDisplayedLog] = createSignal<string>("")
  let logDivRef!: HTMLDivElement;

  createEffect(() => {
    console.log(`Displayed job set to ${displayedJobId}`)
  })

  const fetchJobsQuery = useQuery<GetAllFetchNovelJobsReturnType[]>(() => ({
    queryKey: ['novel-fetch-jobs'],
    queryFn: getAllFetchNovelJobs,
    refetchInterval: 5 * 1000, // 5s
    throwOnError: true, // Throw an error if the query fails
  }))

  // Create dependent array from updateJobsQuery to build a guaranteed existent jobs array
  const fetchJobs = createMemo<GetAllFetchNovelJobsReturnType[]>(() => {
    return fetchJobsQuery.data || []
  })

  // Use above to run parallel queries on job logs with variable refetch interval for logs
  const jobStatuses = useQueries(() => ({
    queries: fetchJobs().map(job => ({
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

  const displayedJob = createMemo< JobStatusReturnType | null>(() => {
    const matchingJob = jobStatuses.find(job => job.data?.jobId === displayedJobId())?.data || null
    return matchingJob
  })

  // Scroll to bottom of log if log changes
  createEffect(() => {
    if (!!(displayedJob()) && displayedLog() !== displayedJob()?.log) {
      setDisplayedLog(displayedJob()!.log || "")
      if (logDivRef) {
        logDivRef.scrollTop = logDivRef.scrollHeight
      }
    }
  })

  return (
    <div id="novels-table-wrapper">
      <h1>追加中の小説</h1>
      <AddFetchNovelSection />
      <ErrorBoundary fallback={<div>エラーが発生しました</div>}>
        <Suspense fallback={<div style="width: 100%; height: 100%;" data-spinner="overlay"></div>}>
          <output data-table-selected aria-live="polite"></output>
          <ot-table 
            empty-text='追加中の小説はありません'
          >

            <div class="table">
              <table>
                <thead>
                  <tr>
                    <th scope="col">開始時刻</th>
                    <th scope="col">URL</th>
                    <th scope="col">取得状況</th>
                    <th scope="col">最新ログ</th>
                    <th scope="col">ログ全文</th>
                  </tr>
                </thead>

                <tbody>
                  <For each={fetchJobsQuery.data?.filter(entry => !!jobStatuses.find(job => job.data?.jobId === entry.jobId))}>
                  {(entry => (
                    <tr>
                      <td data-sort={entry.enqueuedAt.toISOString()}>{entry.enqueuedAt.toLocaleString()}</td>
                      <td data-sort={entry.sourceUrl}>{entry.sourceUrl}</td>
                      <td data-sort={entry.status}><RqJobStatusBadge status={entry.status}/></td>
                      <td>{jobStatuses.find(job => job.data?.jobId === entry.jobId)?.data?.log.split('\n').pop()}</td>
                      <td class="hstack gap-2">
                        <button class="outline" commandfor="log-dialog" command="show-modal" onClick={() => setDisplayedJobId(entry.jobId)}><IconNotebook />ログを表示</button>
                      </td>
                    </tr>
                  ))}
                  </For>

                </tbody>

              </table>
            </div>
          </ot-table>
          <dialog id="log-dialog" closedby="any" style="width: min(100% - 2rem, 64rem);">
            <form method="dialog">
              <header>
                <h3>ログ</h3>
                <p>{displayedJob() === null ? "" : (fetchJobsQuery.data?.find(entry => entry.jobId === displayedJobId())?.sourceUrl || "")}</p>
              </header>
              <div style="max-height: 600px; overflow-y: scroll" ref={logDivRef}>
                <pre style="white-space: pre-wrap;">{displayedJob()?.log}</pre>
              </div>
              <footer>
                <button type="button" commandfor="log-dialog" command="close" class="outline">✕</button>
              </footer>
            </form>
          </dialog>
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

export default NovelsFetchingPage
