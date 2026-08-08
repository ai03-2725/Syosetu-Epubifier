import type { Novel } from "../types/novel"

export const novelBackendStatusToJaStr = (status: string) => {
  switch(status) {
    case "ACTIVE":
      return '連載中'
    case "COMPLETED":
      return '完結'
    case "ABANDONED":
      return '未完'
    default:
      throw new Error(`NovelStatusTools: Unknown status ${status}`)
  }
}

export const novelStatusToSortableInt = (status: Novel["status"]) => {
  switch(status) {
    case "連載中":
      return 0
    case "完結":
      return 1
    case "未完":
      return 2
  }
}