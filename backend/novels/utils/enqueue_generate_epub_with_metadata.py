

from datetime import datetime
import time
import django_rq

from novels.models import Novel
from novels.tasks.syosetu_org.process.generate_epub import generate_epub_syosetu_org
from novels.utils.determine_novel_source import NovelSources, determine_novel_source
from novels.utils.enqueue_job_with_metadata_types import THREE_DAYS_IN_SECONDS, JobIdAndError, JobIdsAndError


def _enqueue_all_generate_tasks(novels_to_update: list[Novel]):
    
    job_ids: list[str] = []
    
    for novel in novels_to_update:
        novel_source = determine_novel_source(novel.source)
        match(novel_source["source"]):
            case NovelSources.SYOSETU_ORG:
                enqueued_task = django_rq.enqueue(generate_epub_syosetu_org, novel.id, result_ttl=THREE_DAYS_IN_SECONDS)
                enqueued_task.meta["enqueued_at"] = datetime.now()
                enqueued_task.meta["task_type"] = "generate_epub_for_novel"
                enqueued_task.meta["novel_id"] = novel.id
                enqueued_task.save()
                job_ids.append(enqueued_task.id)
            case _:
                return {"job_ids": None, "error": f"小説ID{novel.id}の取得先を判別できませんでした"}
            
    return {"job_ids": job_ids, "error": None}
    

            
def enqueue_generate_epub_task(novel_ids: list[int] | bool) -> JobIdsAndError:
    # Synchronous variant that uses Novel.objects.get()
    
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
            
    return _enqueue_all_generate_tasks(novels_to_update)
        
        
async def enqueue_generate_epub_task_async(novel_ids: list[int] | bool) -> JobIdsAndError:
    # Asynchronous variant that uses Novel.objects.aget()
    
    novels_to_update: list[Novel] = []
        
    if isinstance(novel_ids, list):
        for novel_id in novel_ids:
            try:
                novel = await Novel.objects.aget(id=novel_id)
                novels_to_update.append(novel)
            except Novel.DoesNotExist:
                return {"job_ids": None, "error": f"指定された小説{str(novel_id)}は存在しません"}
    else: 
        novels_to_update = [entry async for entry in Novel.objects.filter(frozen=False)]
            
    return _enqueue_all_generate_tasks(novels_to_update)