from enum import Enum
from typing import TypedDict
from urllib.parse import urlparse
import re

class NovelSources(Enum):
    SYOSETU_ORG = "syosetu.org"
    
class NovelSourceReturnType(TypedDict):
    source: NovelSources
    id: str

def determine_novel_source(url: str) -> NovelSourceReturnType | None:
    """
    Determines the novel source
    """
    
    urlparsed = urlparse(url)
    match urlparsed.hostname:
        
        case "syosetu.org":
            
            # Look for "https://syosetu.org/novel/id_num/..."
            novel_id_pattern_match = re.search(r"^\/novel\/(?P<id>\d+)", urlparsed.path)
            if novel_id_pattern_match:
                return NovelSourceReturnType(
                    source=NovelSources.SYOSETU_ORG,
                    id=int(novel_id_pattern_match.group("id"))
                )
            
            # Look for "https://syosetu.org/?mode=...&nid=413594"
            novel_nid_pattern_match = re.search(r"nid=(?P<id>\d+)", urlparsed.query)
            if novel_nid_pattern_match:
                return NovelSourceReturnType(
                    source=NovelSources.SYOSETU_ORG,
                    id=int(novel_nid_pattern_match.group("id"))
                )
            
            # Domain was matched but novel ID wasn't found in URL
            raise Exception("Matched domain but couldn't determine ID")
            
        case _:
            return None
