import type { Component } from "solid-js";
import type { RqJobStatus } from "../types/rq-job-statuses";


export const RqJobStatusBadge: Component<{status: RqJobStatus}> = (props) => {

  switch (props.status) {
    case "canceled":
      return <span class="badge" data-variant="warning">キャンセル済み</span>
    case "created":
      return <span class="badge" data-variant="secondary">タスク作製済み</span>
    case "deferred":
      return <span class="badge" data-variant="warning">タスク延期中</span>
    case "failed":
      return <span class="badge" data-variant="danger">失敗</span>
    case "finished":
      return <span class="badge" data-variant="success">完了</span>
    case "queued":
      return <span class="badge">順番待ち</span>
    case "scheduled":
      return <span class="badge outline">スケジュール済み</span>
    case "started":
      return <span class="badge">実行中</span>
    case "stopped":
      return <span class="badge" data-variant="secondary">停止中</span>
    default:
      return <span class="badge" data-variant="secondary">{props.status}</span>
  }

}