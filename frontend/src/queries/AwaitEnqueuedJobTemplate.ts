import type { RqJobStatus } from "../types/rq-job-statuses"

export async function awaitEnqueuedJob<T>(postEndpoint: string, postBody: object, pollEndpoint: string, pollIntervalMs: number = 1000) {
  // First POST to the start-epub endpoint
  const result = await fetch(postEndpoint, {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(postBody),
  })
  if (!result.ok) throw new Error('タスク開始に失敗しました：' + JSON.stringify(result.json()))
  // Get the job_id field from return value
  return await result.json()
  // Then check that the data has a jobId field
    .then((data) => {
      if (!Object.hasOwn(data, "jobId")) {
        throw new Error('Returned object does not have a jobId field')
      }
      return data.jobId
    })
    .then(async (jobId: string) => {
      // Await completion on this given job
      while (true) {
          const result = await fetch(pollEndpoint + `?jobId=${jobId}`, {
          method: "GET",
        })
        const resultData = await result.json()
        const jobStatus: RqJobStatus = resultData.status

        // Check the job status 
        switch(jobStatus) {
          
          case "scheduled":
          case "deferred":
          case "queued":
          case "created":
          case "started":
          default:
            // Default action = Do nothing, await next loop
            break;  
          
          case "canceled":
          case "failed":
          case "stopped":
            // Handle failures
            throw new Error(`タスクが失敗しました: ${JSON.stringify(resultData)}`)

          case "finished":
            // Handle success
            return resultData as T
        }

        await new Promise(r => setTimeout(r, pollIntervalMs));
      }
    })
}
