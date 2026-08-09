

from rq import get_current_job
from django.conf import settings

def append_to_job_log(msg: str):
    """
    Append text to the rq job meta log object
    Also logs the message if settings.LOG_DEBUG is True
    """
    print(msg)
    job = get_current_job()
    if job:
        if type(job.meta.get('log')) is not str:
            job.meta['log'] = ""
        job.meta['log'] = job.meta['log'] + '\n' + msg
        job.save()