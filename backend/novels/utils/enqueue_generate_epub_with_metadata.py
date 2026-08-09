

from datetime import datetime
import time
import django_rq

from novels.models import Novel
from novels.tasks.syosetu_org.process.generate_epub import generate_epub_syosetu_org
from novels.utils.determine_novel_source import NovelSources, determine_novel_source
from novels.utils.enqueue_job_with_metadata_types import THREE_DAYS_IN_SECONDS, JobIdAndError

            
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
            time.sleep(1)
            return {"error": None, "job_id": enqueued_task.id}
        case _:
            return {"job_id": None, "error": f"小説ID{novel.id}の取得先を判別できませんでした"}