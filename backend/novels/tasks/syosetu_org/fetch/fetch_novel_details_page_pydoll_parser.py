
from typing import NamedTuple

from pydoll.browser.tab import Tab
from novels.tasks.syosetu_org.fetch.fetch_path_with_tab import fetch_path_with_tab
from novels.utils.append_to_job_log import append_to_job_log

from novels.models import NovelStatusChoices


class FetchNovelDetailsReturnType(NamedTuple):
    title: str
    author: str
    status: NovelStatusChoices

async def fetch_novel_details_page_pydoll(tab: Tab, id: int) -> FetchNovelDetailsReturnType:
    """
    Fetch novel details from details page: title, author, status, overview text
    """
    append_to_job_log(f"小説情報を取得中")
    await fetch_path_with_tab(f'https://syosetu.org/?mode=ss_detail&nid={str(id)}', tab)
    
    # Get novel details
    # Structure: Updated 2026-07-31
    # First table occurrence (class "table1") -> tbody -> 
    # - First tr -> Second td -> a -> inner text = Novel title
    # - Second tr -> Fourth td -> a -> inner text = Author
    # - Third tr -> Second td = Novel overview text (raw, likely need to wrap in <p> for epub)
    #   - Currently not scanned - fetched from index page instead
    # Second table occurrence (class "table1") -> tbody -> 
    # - First tr -> Fourth td = Novel status (for example "連載(連載中) 50話")
    # Ignore most recent post since most recent update can't be scanned from here anyways
    
    title = await (await tab.query("//table[@class='table1'][1]/tbody/tr[1]/td[2]/a")).text
    author = await (await tab.query("//table[@class='table1'][1]/tbody/tr[2]/td[4]/a")).text
    # overview_raw = await (await tab.query("//table[@class='table1'][1]/tbody/tr[3]/td[2]")).inner_html # Includes starting/ending TDs
    # overview = overview_raw.removeprefix('<td colspan="3">').removesuffix('</td>')
    
    status_raw = await (await tab.query("//table[@class='table1'][2]/tbody/tr[1]/td[4]")).text
    status: NovelStatusChoices = NovelStatusChoices.ACTIVE.name
    if "連載中" in status_raw:
        status = NovelStatusChoices.ACTIVE.name
    elif "完結" in status_raw:
        status = NovelStatusChoices.COMPLETED.name
    elif "未完" in status_raw:
        status = NovelStatusChoices.ABANDONED.name
    else:
        raise Exception(f"Unknown novel status in string {status_raw}")
    
    append_to_job_log(f"小説情報の取得完了")    
    return FetchNovelDetailsReturnType(title=title, author=author, status=status)