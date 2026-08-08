import { BACKEND_IP } from ".."
import type { JobStatusReturnType } from "../types/rq-job-statuses"
import { awaitEnqueuedJob } from "./AwaitEnqueuedJobTemplate"


export const awaitEpubGen = async (novel_id: number) => {
  // Use the enqueued job template to await
  const result = await awaitEnqueuedJob<JobStatusReturnType>(
    BACKEND_IP + '/novel/generate-epub/',
    { novelId: novel_id },
    BACKEND_IP + '/novel/job-status/',
    1000
  )
  return
}

