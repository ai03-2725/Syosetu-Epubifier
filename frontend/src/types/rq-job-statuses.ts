const RqJobStatusList = {
  CREATED: 'created',
  QUEUED: 'queued',
  FINISHED: 'finished',
  FAILED: 'failed',
  STARTED: 'started',
  DEFERRED: 'deferred',
  SCHEDULED: 'scheduled',
  STOPPED: 'stopped',
  CANCELED: 'canceled',
} as const;

export type RqJobStatus = typeof RqJobStatusList[keyof typeof RqJobStatusList]

export type JobStatusReturnType = {
  jobId: string,
  status: RqJobStatus,
  taskType: string,
  log: string,
  enqueuedAt: Date,
}