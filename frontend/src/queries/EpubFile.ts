import { BACKEND_IP } from "..";
import type { EpubFile } from "../types/epub-file";


export async function getAllEpubFiles(): Promise<EpubFile[]> {
  const result = await fetch(BACKEND_IP + '/novel/epub-files/')
  if (!result.ok) throw new Error('epubリストの取得に失敗しました：' + JSON.stringify(result.json()))
  return await result.json()
    .then(data => {
      return data.map((entry: any) => {
        return {
          id: entry.id,
          novel: entry.novel,
          file: entry.file
        }
      })
    })
}