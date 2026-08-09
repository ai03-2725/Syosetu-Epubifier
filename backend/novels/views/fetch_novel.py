
import django_rq
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from url_normalize import url_normalize

from novels.utils.enqueue_fetch_novel_with_metadata import enqueue_fetch_novel_task
from novels.utils.get_all_job_ids import get_all_job_ids


@api_view(['POST'])
def start_fetch_novel_task(request: Request):
    """
    Starts a fetch-novel task for a new novel
    """

    if request.method != "POST":
        return Response(status=400)
    
    novel_url = request.data.get("novelUrl")
    if novel_url is None:
        return Response({"error": "novelUrlを指定してください"}, status=400)
    novel_url = url_normalize(novel_url)
    
    return_value = enqueue_fetch_novel_task(novel_url)
    return Response({"error": return_value["error"], "jobId": return_value["job_id"]}, status=200 if return_value["error"] is None else 400, )

@api_view(['GET'])
def get_all_fetch_novel_tasks(request: Request):
    """
    Gets all running fetch-new-novel task IDs
    """
    queue = django_rq.get_queue("default")
    
    job_ids = get_all_job_ids()
    fetch_novel_jobs = [queue.fetch_job(job_id) for job_id in job_ids if queue.fetch_job(job_id).meta.get("task_type") == "fetch_new_novel"]
            
    return Response([{
        "job_id": job.id,
        "source_url": job.meta.get("source_url"),
        "status": job.get_status(),
        "enqueued_at": job.meta.get("enqueued_at").isoformat(),
        # "log": job.meta.get("log", "")
    } for job in fetch_novel_jobs])