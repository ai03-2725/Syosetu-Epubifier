import { BACKEND_IP } from ".."
import type { RqJobStatus } from "../types/rq-job-statuses"


export type GetAllFetchNovelJobsReturnType = {
  jobId: string,
  sourceUrl: string,
  status: RqJobStatus,
  enqueuedAt: Date
}

export async function getAllFetchNovelJobs(): Promise<GetAllFetchNovelJobsReturnType[]> {
  const result = await fetch(BACKEND_IP + '/novel/all-fetch-tasks/')
  if (!result.ok) throw new Error('追加中の小説リストの取得に失敗しました：' + JSON.stringify(result.json()))
  return await result.json()
    .then(data => {
      return data.map((entry: any) => {
        return {
          jobId: entry.job_id,
          sourceUrl: entry.source_url,
          status: entry.status,
          enqueuedAt: new Date(entry.enqueued_at)
        }
      })
    })
}

export async function enqueueNovelFetchTask(novelUrl: string): Promise<string[]> {
  // Send novelIds = true to update all possible novels
  const result = await fetch(BACKEND_IP + '/novel/new-novel/', {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({novelUrl: novelUrl}),
  })
  if (!result.ok) throw new Error('追加開始に失敗しました：' + JSON.stringify(result.json()))
    return await result.json()
      .then(data => data.job_ids)
}