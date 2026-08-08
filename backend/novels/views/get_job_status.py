from datetime import datetime

import django_rq
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rq.job import Job


@api_view(['GET'])
def get_job_status(request: Request):
    """
    Gets the current status of a novel task
    """
    if request.method != "GET":
        return Response(status=400)
    
    job_id = request.query_params.get("jobId", None)
    if job_id is None:
        return Response({"error": "jobIdを指定してください。"}, status=400)
    
    job: Job | None = django_rq.get_queue("default").fetch_job(job_id)
    if job is None:
        return Response({"error": "指定されたjobIdは見つかりませんでした。"}, status=404)
    
    job_log = job.meta.get("log", "")
    job_status = job.get_status()    
    enqueued_at_timestamp: datetime = job.meta.get("enqueued_at")
    
    response_object = {
        "job_id": job_id, 
        "status": job_status, 
        "task_type": job.meta.get("task_type"), 
        "log": job_log,
        "enqueued_at": enqueued_at_timestamp.isoformat()
    }
    
    return Response(response_object, status=200)