import { BACKEND_IP } from ".."
import type { JobStatusReturnType } from "../types/rq-job-statuses"

export async function getJobStatus(jobId: string): Promise<JobStatusReturnType> {
  const result = await fetch(BACKEND_IP + '/novel/job-status/?jobId=' + jobId)
  if (!result.ok) throw new Error('タスク状況の取得に失敗しました：' + JSON.stringify(result.json()))
  return await result.json()
    .then(data => {
      return {
        jobId: data.job_id,
        status: data.status,
        taskType: data.task_type,
        log: data.log,
        enqueuedAt: new Date(data.enqueued_at)
      }
    })
}