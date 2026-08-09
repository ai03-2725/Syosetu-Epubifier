

from datetime import datetime
import time
from typing import TypedDict
import django_rq

from novels.models import Novel
from novels.tasks.syosetu_org.fetch.update_existing_novel import update_existing_novel_syosetu_org
from novels.utils.determine_novel_source import NovelSources, determine_novel_source
from novels.utils.enqueue_job_with_metadata_types import THREE_DAYS_IN_SECONDS, THREE_HOURS_IN_SECONDS, JobIdsAndError

        
        
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
                enqueued_task = django_rq.enqueue(update_existing_novel_syosetu_org, novel_source["id"], allow_delete, result_ttl=THREE_DAYS_IN_SECONDS, job_timeout=THREE_HOURS_IN_SECONDS)
                enqueued_task.meta["enqueued_at"] = datetime.now()
                enqueued_task.meta["task_type"] = "update_existing_novel"
                enqueued_task.meta["novel_id"] = novel.id
                enqueued_task.save()
                time.sleep(1)
                job_ids.append(enqueued_task.id)
            case _:
                return {"job_ids": None, "error": f"小説ID{novel.id}の取得先を判別できませんでした"}
    
    return {"job_ids": job_ids, "error": None}
            
