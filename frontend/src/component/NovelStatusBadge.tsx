import type { Component } from "solid-js"
import type { Novel } from "../types/novel"

export const NovelStatusBadge: Component<{
  status: Novel["status"]
}> = (props) => {
  switch (props.status) {
    case "連載中":
      return (<span class="badge" data-variant="secondary">連載中</span>)
    case "完結":
      return (<span class="badge" data-variant="success">完結</span>)
    case "未完":
      return (<span class="badge outline">未完</span>)
    default:
      throw new Error(`NovelStatusBadge: Unknown novel status "${props.status}"`)
  }
}