import { BACKEND_IP } from ".."
import type { JobStatusReturnType } from "../types/rq-job-statuses"
import { awaitEnqueuedJobs } from "./AwaitEnqueuedJobsTemplate"


export const awaitEpubGen = async (novel_ids: number[] | true) => {
  // Use the enqueued job template to await
  const errors = await awaitEnqueuedJobs(
    BACKEND_IP + '/novel/generate-epub/',
    { novelIds: novel_ids },
    BACKEND_IP + '/novel/job-status/',
    500
  )
  return errors
}

