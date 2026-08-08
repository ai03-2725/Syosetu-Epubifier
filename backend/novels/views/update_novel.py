
import django_rq
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from novels.utils.enqueue_job_with_metadata import enqueue_update_novel_tasks
from novels.utils.get_all_job_ids import get_all_job_ids


@api_view(['POST'])
def start_update_novels_task(request: Request):
    """
    Starts a fetch-novel task for an existing novel
    novelIds can either be a list of novel IDs or the boolean True for auto-select every unfrozen novel
    """

    if request.method != "POST":
        return Response(status=400)
    
    novel_ids = request.data.get("novelIds")
    # Handle cases where novelIds simply isn't defined
    if novel_ids is None:
        return Response({"error": "novelIdsを指定してください"}, status=400)
    # Handle case where novelIds is True = autofetch all - proceed as-is
    elif isinstance(novel_ids, bool) and novel_ids is True:
        pass
    # Otherwise novelIds should be a list of IDs
    # Handle cases where it isn't
    elif not isinstance(novel_ids, list) or not all(isinstance(novel_id, int) for novel_id in novel_ids):
        return Response({"error": "novelIdsはIDのリストかTrueとして指定ください"}, status=400)
    # Otherwise should be fine
    
    allow_delete = request.data.get("allowDelete", False)
    
    return_value = enqueue_update_novel_tasks(novel_ids, allow_delete)
    return Response({"error": return_value["error"], "jobIds": return_value["job_ids"]}, status=200 if return_value["error"] is None else 400)

@api_view(['GET'])
def get_all_update_novel_tasks(request: Request):
    """
    Gets all running fetch-new-novel task IDs
    """
    queue = django_rq.get_queue("default")
    
    job_ids = get_all_job_ids()
    fetch_novel_jobs = [queue.fetch_job(job_id) for job_id in job_ids if queue.fetch_job(job_id).meta.get("task_type") == "update_existing_novel"]
    
    return Response([{
        "job_id": job.id,
        "novel_id": job.meta.get("novel_id"),
        "status": job.get_status(),
        "enqueued_at": job.meta.get("enqueued_at").isoformat()
        # "log": job.meta.get("log", "")
    } for job in fetch_novel_jobs])