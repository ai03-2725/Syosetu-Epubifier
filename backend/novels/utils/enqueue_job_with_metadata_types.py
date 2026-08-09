

from typing import TypedDict
    
THREE_DAYS_IN_SECONDS = 60 * 60 * 24 * 3
THREE_HOURS_IN_SECONDS = 60 * 60 * 3
    
class JobIdAndError(TypedDict):
    job_id: str | None
    error: str | None
    
class JobIdsAndError(TypedDict):
    job_ids: list[str] | None
    error: str | None

    
