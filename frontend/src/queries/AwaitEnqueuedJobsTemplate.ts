import type { RqJobStatus } from "../types/rq-job-statuses"

export async function awaitEnqueuedJobs(postEndpoint: string, postBody: object, pollEndpoint: string, pollIntervalMs: number = 500) {
  // Awaits an enqueue endpoint that returns multiple job IDs
  // Returns a list of error strings (empty if success)

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
      if (!Object.hasOwn(data, "jobIds")) {
        throw new Error('Returned object does not have a jobIds field')
      }
      return data.jobIds
    })
    .then(async (jobIds: string[]) => {
      let pendingJobs = [...jobIds]
      let errors: string[] = []
      // Await completion on all given jobs
      // Cycle through fetches in order with some delay in between
      let currentIndex = 0
      while (pendingJobs.length > 0) {
        // Keep track of how much time each loop takes to ensure a minimum delay
        const result = await fetch(pollEndpoint + `?jobId=${pendingJobs[currentIndex]}`, {
          method: "GET",
        })
        const resultData = await result.json()
        const jobStatus: RqJobStatus = resultData.status

        // Check the job status 
        switch(jobStatus) {
          
          case "canceled":
          case "failed":
          case "stopped":
            // Handle failures
            errors.push(`タスクが失敗しました: ${JSON.stringify(resultData)}`)
            pendingJobs.splice(currentIndex)
            break;

          case "finished":
            // Handle success
            pendingJobs.splice(currentIndex)
            break;

          case "scheduled":
          case "deferred":
          case "queued":
          case "created":
          case "started":
          default:
            // Default action = Do nothing, await next loop
            break;  
        }

        currentIndex += 1
        // If already did one full loop through the jobs, delay and restart from job 0
        if (currentIndex >= pendingJobs.length) {
          currentIndex = 0
        }

        await new Promise(r => setTimeout(r, pollIntervalMs));
      }
      return errors
    })
}
