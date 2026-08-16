
from typing import NamedTuple

from bs4 import BeautifulSoup
from pydoll.browser.tab import Tab
from novels.tasks.syosetu_org.fetch.fetch_path_with_tab import fetch_path_with_tab
from novels.utils.append_to_job_log import append_to_job_log

# from novels.models import NovelStatusChoices


class FetchNovelDetailsReturnType(NamedTuple):
    title: str
    author: str
    # status: NovelStatusChoices

async def fetch_novel_details_page(tab: Tab, id: int) -> FetchNovelDetailsReturnType:
    """
    Fetch novel details from details page: title, author, status, overview text
    """
    append_to_job_log(f"小説情報を取得中")
    await fetch_path_with_tab(f'https://syosetu.org/?mode=ss_detail&nid={str(id)}', tab)
    
    html_content = await tab.page_source
    
    # Parse using BS4 - matching using pydoll wasn't always reliable
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get novel details
    # Structure: Updated 2026-07-31
    # - td with inner text "タイトル" -> Next td -> inner text = Title
    # - td with inner text "作者" -> Next td -> a -> inner text = Author
    # - td with inner text "話数" -> Next td -> inner text = Novel status (for example "連載(連載中) 50話")
    
    title_label_td = soup.find('td', string="タイトル")
    title = title_label_td.find_next_sibling('td').get_text() # Can ignore the a wrapper since bs4 fetches the inner text directly
    
    author_label_td = soup.find('td', string="作者")
    author = author_label_td.find_next_sibling('td').get_text()
    
    # status_label_td = soup.find('td', string="話数")
    # status_raw = status_label_td.find_next_sibling('td').get_text()
    
    # status: NovelStatusChoices = NovelStatusChoices.ACTIVE.name
    # if "連載中" in status_raw:
    #     status = NovelStatusChoices.ACTIVE.name
    # elif "完結" in status_raw:
    #     status = NovelStatusChoices.COMPLETED.name
    # elif "未完" in status_raw:
    #     status = NovelStatusChoices.ABANDONED.name
    # else:
        # raise Exception(f"Unknown novel status in string {status_raw}")
    
    append_to_job_log(f"小説情報の取得完了")    
    # return FetchNovelDetailsReturnType(title=title, author=author, status=status)
    return FetchNovelDetailsReturnType(title=title, author=author)