import { BACKEND_IP } from "..";
import type { Novel } from "../types/novel";


export async function getAllNovels(): Promise<Novel[]> {
  const result = await fetch(BACKEND_IP + '/novel/novels/')
  if (!result.ok) throw new Error('小説リストの取得に失敗しました：' + JSON.stringify(result.json()))
  return await result.json()
    .then(data => {
      return data.map((entry: any) => {
        return {
          id: entry.id,
          title: entry.title,
          author: entry.author,
          source: entry.source,
          tags: entry.tags as string[],
          lastUpdatedTimestamp: new Date(entry.last_updated_timestamp),
          lastFetchTimestamp: new Date(entry.last_fetch_timestamp),
          frozen: entry.frozen, 

          postprocessReduceBlankLines: entry.postprocess_reduce_blank_lines,
          postprocessIndentSeparators: entry.postprocess_indent_separators,
          postprocessReplaceHrs: entry.postprocess_replace_hrs, 
          postprocessAutoIndent: entry.postprocess_auto_indent, 
        }
      })
    })
}

export async function toggleNovelFrozenState(novel: Novel): Promise<Novel> {
  const result = await fetch(BACKEND_IP + `/novel/novels/${novel.id}/`, {
    method: "PATCH",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({frozen: !novel.frozen}),
  })
  if (!result.ok) throw new Error('小説リストの凍結状態の更新に失敗しました：' + JSON.stringify(result.json()))
  return await result.json()
    .then(entry => {
      return {
        id: entry.id,
        title: entry.title,
        author: entry.author,
        source: entry.source,
        tags: entry.tags as string[],
        lastUpdatedTimestamp: new Date(entry.last_updated_timestamp),
        lastFetchTimestamp: new Date(entry.last_fetch_timestamp),
        frozen: entry.frozen,

        postprocessReduceBlankLines: entry.postprocess_reduce_blank_lines,
        postprocessIndentSeparators: entry.postprocess_indent_separators,
        postprocessReplaceHrs: entry.postprocess_replace_hrs, 
        postprocessAutoIndent: entry.postprocess_auto_indent, 
      }
    })
}

export async function deleteNovel(novelId: number): Promise<void> {
  const result = await fetch(BACKEND_IP + `/novel/novels/${novelId}/`, {
    method: "DELETE",
  })
  if (!result.ok) throw new Error('小説の削除に失敗しました：' + JSON.stringify(result.json()))
  return
}