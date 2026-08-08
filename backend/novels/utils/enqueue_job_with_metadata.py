

from datetime import datetime
from typing import Literal, TypedDict
import django_rq

from novels.models import Novel
from novels.tasks.syosetu_org.fetch.fetch_new_novel import fetch_new_novel_syosetu_org
from novels.tasks.syosetu_org.fetch.update_existing_novel import update_existing_novel_syosetu_org
from novels.tasks.syosetu_org.process.generate_epub import generate_epub_syosetu_org
from novels.utils.determine_novel_source import NovelSources, determine_novel_source
    
THREE_DAYS_IN_SECONDS = 60 * 60 * 24 * 3
    
class JobIdAndError(TypedDict):
    job_id: str | None
    error: str | None
    
class JobIdsAndError(TypedDict):
    job_ids: list[str] | None
    error: str | None

    
def enqueue_fetch_novel_task(source_url: str) -> JobIdAndError:
    """
    Enqueue a fetch novel task with proper metadata
    """
    
    try:
        existing_novel = Novel.objects.get(source=source_url)
        if existing_novel is not None:
            return {"job_id": None, "error": "すでに登録されている小説です"}
    except Novel.DoesNotExist:
        pass
    
    novel_source = determine_novel_source(source_url)
    if novel_source is None:
        return None
    
    match(novel_source["source"]):
        case NovelSources.SYOSETU_ORG:
            enqueued_task = django_rq.enqueue(fetch_new_novel_syosetu_org, novel_source["id"], result_ttl=THREE_DAYS_IN_SECONDS)
            enqueued_task.meta["enqueued_at"] = datetime.now()
            enqueued_task.meta["task_type"] = "fetch_new_novel"
            enqueued_task.meta["source_url"] = source_url
            enqueued_task.save()
            return {"job_id": enqueued_task.id, "error": None}
            
        case _: 
            return {"job_id": None, "error": "指定されたURLを識別できませんでした。\n現在対応しているサイト：\n" + "\n".join([source.value for source in NovelSources])}
        
        
def enqueue_update_novel_tasks(novel_ids: list[int] | bool, allow_delete: bool) -> JobIdsAndError:
    """
    Enqueue update novel tasks with proper metadata
    novel_ids = either a list of novel IDs or True for update-all
    Returns a list of job_ids if succeeds (or None if fails)
    """
    novels_to_update: list[Novel] = []
    
    if isinstance(novel_ids, list):
        for novel_id in novel_ids:
            try:
                novel = Novel.objects.get(id=novel_id)
                novels_to_update.append(novel)
            except Novel.DoesNotExist:
                return {"job_ids": None, "error": f"指定された小説{str(novel_id)}は存在しません"}
    else: 
        novels_to_update = list(Novel.objects.filter(frozen=False))
        
    job_ids: list[str] = []
    
    for novel in novels_to_update:
        novel_source = determine_novel_source(novel.source)
        match(novel_source["source"]):
            case NovelSources.SYOSETU_ORG:
                enqueued_task = django_rq.enqueue(update_existing_novel_syosetu_org, novel_source["id"], allow_delete, result_ttl=THREE_DAYS_IN_SECONDS)
                enqueued_task.meta["enqueued_at"] = datetime.now()
                enqueued_task.meta["task_type"] = "update_existing_novel"
                enqueued_task.meta["novel_id"] = novel.id
                enqueued_task.save()
                job_ids.append(enqueued_task.id)
            case _:
                return {"job_ids": None, "error": f"小説ID{novel.id}の取得先を判別できませんでした"}
    
    return {"job_ids": job_ids, "error": None}
            
            
def enqueue_generate_epub_task(novel_id: int) -> JobIdAndError:
    novel = Novel.objects.get(id=novel_id)
    novel_source = determine_novel_source(novel.source)
    match(novel_source["source"]):
        case NovelSources.SYOSETU_ORG:
            enqueued_task = django_rq.enqueue(generate_epub_syosetu_org, novel_id, result_ttl=THREE_DAYS_IN_SECONDS)
            enqueued_task.meta["enqueued_at"] = datetime.now()
            enqueued_task.meta["task_type"] = "generate_epub_for_novel"
            enqueued_task.meta["novel_id"] = novel_id
            enqueued_task.save()
            return {"error": None, "job_id": enqueued_task.id}
        case _:
            return {"job_id": None, "error": f"小説ID{novel.id}の取得先を判別できませんでした"}