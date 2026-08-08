
import django_rq


def get_all_job_ids():
    """
    Collects all job IDs from all registries
    """
    queue = django_rq.get_queue("default")
        
    job_ids: list[str] = []
    job_ids.extend(queue.started_job_registry.get_job_ids())
    job_ids.extend(queue.deferred_job_registry.get_job_ids())
    job_ids.extend(queue.finished_job_registry.get_job_ids())
    job_ids.extend(queue.failed_job_registry.get_job_ids())
    job_ids.extend(queue.scheduled_job_registry.get_job_ids())
    job_ids.extend(queue.canceled_job_registry.get_job_ids())
    return job_ids
    
def get_all_realtime_job_ids():
    """
    Collects all job IDs from registries that aren't for future execution at a set time
    """
    queue = django_rq.get_queue("default")
        
    job_ids: list[str] = []
    job_ids.extend(queue.started_job_registry.get_job_ids())
    job_ids.extend(queue.deferred_job_registry.get_job_ids())
    job_ids.extend(queue.finished_job_registry.get_job_ids())
    job_ids.extend(queue.failed_job_registry.get_job_ids())
    job_ids.extend(queue.canceled_job_registry.get_job_ids())
    return job_ids