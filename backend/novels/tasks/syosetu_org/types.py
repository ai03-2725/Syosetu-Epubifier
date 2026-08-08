import datetime
from typing import TypedDict


class DraftEpisode(TypedDict):
    episode_number: int
    chapter_number: int
    title: str
    last_updated: datetime.datetime | None
    href: str | None
    contents: str | None
    
class DraftChapter(TypedDict):
    chapter_number: int
    title: str | None