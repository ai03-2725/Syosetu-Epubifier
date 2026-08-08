import { BACKEND_IP } from ".."
import type { RqJobStatus } from "../types/rq-job-statuses"


export type GetAllUpdateNovelJobsReturnType = {
  jobId: string,
  novelId: number,
  status: RqJobStatus,
  enqueuedAt: Date
}

export async function getAllUpdateNovelJobs(): Promise<GetAllUpdateNovelJobsReturnType[]> {
  const result = await fetch(BACKEND_IP + '/novel/all-update-tasks/')
  if (!result.ok) throw new Error('更新中の小説リストの取得に失敗しました：' + JSON.stringify(result.json()))
  return await result.json()
    .then(data => {
      return data.map((entry: any) => {
        return {
          jobId: entry.job_id,
          novelId: entry.novel_id,
          status: entry.status,
          enqueuedAt: new Date(entry.enqueued_at)
        }
      })
    })
}

export async function enqueueNovelUpdateTask(novelIds: number[] | true): Promise<string[]> {
  // Send novelIds = true to update all possible novels
  const result = await fetch(BACKEND_IP + '/novel/update-novels/', {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({novelIds: novelIds}),
  })
  if (!result.ok) throw new Error('更新開始に失敗しました：' + JSON.stringify(result.json()))
    return await result.json()
      .then(data => data.job_ids)
}