

from datetime import datetime
import time
import django_rq

from novels.models import Novel
from novels.tasks.syosetu_org.fetch.fetch_new_novel import fetch_new_novel_syosetu_org
from novels.utils.determine_novel_source import NovelSources, determine_novel_source
from novels.utils.enqueue_job_with_metadata_types import THREE_DAYS_IN_SECONDS, THREE_HOURS_IN_SECONDS, JobIdAndError
    

    
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
            enqueued_task = django_rq.enqueue(fetch_new_novel_syosetu_org, novel_source["id"], result_ttl=THREE_DAYS_IN_SECONDS, job_timeout=THREE_HOURS_IN_SECONDS)
            enqueued_task.meta["enqueued_at"] = datetime.now()
            enqueued_task.meta["task_type"] = "fetch_new_novel"
            enqueued_task.meta["source_url"] = source_url
            enqueued_task.save()
            return {"job_id": enqueued_task.id, "error": None}
            
        case _: 
            return {"job_id": None, "error": "指定されたURLを識別できませんでした。\n現在対応しているサイト：\n" + "\n".join([source.value for source in NovelSources])}
        
        
