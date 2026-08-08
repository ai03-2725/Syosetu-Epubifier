
import re

def source_to_id(source_url: str):
    
    # print(source_url)
    
    # Look for "https://syosetu.org/novel/id_num/..."
    novel_id_pattern_match = re.search(r"\/novel\/(?P<id>\d+)", source_url)
    if novel_id_pattern_match:
        return int(novel_id_pattern_match.group("id"))

    # Look for "https://syosetu.org/?mode=...&nid=413594"
    novel_nid_pattern_match = re.search(r"nid=(?P<id>\d+)", source_url)
    if novel_nid_pattern_match:
        return int(novel_nid_pattern_match.group("id"))
    
    raise Exception("syosetu.orgのIDを識別できませんでした")