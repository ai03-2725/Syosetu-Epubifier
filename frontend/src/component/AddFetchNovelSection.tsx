import { useQueryClient, useMutation } from "@tanstack/solid-query";
import { createEffect, createSignal, type Component } from "solid-js";
import { BACKEND_IP } from "..";
import { enqueueNovelFetchTask } from "../queries/FetchNovelJobs";

export const AddFetchNovelSection: Component<{

}> = (props) => {
  const queryClient = useQueryClient()
  const [urlField, setUrlField] = createSignal<string>("")
  

  // Always wrap options in a function callback for SolidJS reactivity
  const mutation = useMutation(() => ({
    mutationFn: (novelUrl: string) => enqueueNovelFetchTask(novelUrl),
    onError: (e) => {
      console.error(e);
      (window as any).ot.toast(e.message, '追加に失敗しました', { variant: 'warning', placement: 'bottom-right', duration: 10 * 1000 });
    },
    onSuccess: () => {
      // Invalidate the cache to trigger refetching
      queryClient.invalidateQueries({ queryKey: ['novel-fetch-jobs'] });
      setUrlField("");
      (window as any).ot.toast(`小説の取得を開始しました」`, '追加開始', { variant: 'success', placement: 'bottom-right', duration: 10 * 1000 })
    },
  }))

  return (
    <div>
      <fieldset class="group">
      <legend>小説を追加</legend>
      <input type="text" placeholder="URL" value={urlField()} onInput={(e) => setUrlField(e.currentTarget.value)}/>
      <button onClick={() => mutation.mutate(urlField())} disabled={mutation.isPending} aria-busy={mutation.isPending} data-spinner="small">＋</button>
      </fieldset>
    </div>
  )

}

