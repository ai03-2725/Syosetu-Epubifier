from typing import TypedDict

from bs4 import BeautifulSoup
from django.core.files import File
from pydoll.browser.tab import Tab
from novels.tasks.syosetu_org.types import DraftEpisode
from novels.utils.append_to_job_log import append_to_job_log
from novels.tasks.syosetu_org.fetch.fetch_path_with_tab import fetch_path_with_tab
from novels.models import UploadedImage
from snowflake import SnowflakeGenerator
from url_normalize import url_normalize

    
def find_embedded_images(soup: BeautifulSoup) -> list[str]:
    """
    Looks for embedded images in the provided episode text
    """
    
    # Scan episode for images
    # Look for embedded image URLs in the HTML contents using beautifulsoup
    # print(episode_text)
    # soup = BeautifulSoup(episode_text, "html.parser").find_all(lambda t: t.name == "a" and t.text == "【挿絵表示】")
    a_tags = soup.find_all("a", string="【挿絵表示】")        
    found_image_urls: list[str] = [a.get("href") for a in a_tags if a.get("href") is not None]
    return found_image_urls
    