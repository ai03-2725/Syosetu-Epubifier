from typing import TypedDict

from bs4 import BeautifulSoup
from django.core.files import File
from pydoll.browser.tab import Tab
from novels.tasks.syosetu_org.fetch.intercept_image import fetch_single_embedded_image
from novels.tasks.syosetu_org.process.find_embedded_images import find_embedded_images
from novels.tasks.syosetu_org.types import DraftEpisode
from novels.utils.append_to_job_log import append_to_job_log
from novels.tasks.syosetu_org.fetch.fetch_path_with_tab import fetch_path_with_tab
from novels.models import UploadedImage
from snowflake import SnowflakeGenerator
from url_normalize import url_normalize


class FetchedImage(TypedDict):
    episode: int # The episode in which the image was found
    image_url: str # The original href of the image link
    
async def fetch_embedded_images(tab: Tab, episodes: list[DraftEpisode]) -> dict[int, list[str]]:
    """
    Fetches the embedded images found within the provided episodes; adds them to the db
    Returns a dict of {episode_number: ["url_1", "url_2"...], ...}
    """
    
    # Scan each episode for images
    # Look for embedded image URLs in the HTML contents using beautifulsoup
    image_hrefs_table: dict[int, list[str]] = {}
    append_to_job_log(f'押絵の検出中')
    for episode in episodes:
        soup = BeautifulSoup(episode['contents'], 'html.parser')
        found_image_urls = find_embedded_images(soup)
        if len(found_image_urls) > 0:
            image_hrefs_table[episode["episode_number"]] = found_image_urls
        
    if len(image_hrefs_table) == 0:
        append_to_job_log(f'更新話内に押絵は発見されませんでした')
        return {}
    
    # Handle all found images
    gen = SnowflakeGenerator(100)
    
    for image_urls in image_hrefs_table.values():        
        for image_url in image_urls:
            # Check if the image already exists in the db to avoid duplicate fetching
            normalized_url = url_normalize(image_url)
            try:
                # If exists, pass
                await UploadedImage.objects.aget(source_src=normalized_url)
                append_to_job_log(f'押絵「{image_url}」はすでにダウンロード済み')
                continue
            except UploadedImage.DoesNotExist:
                # If not exists, fetch and upload to db
                append_to_job_log(f'押絵「{image_url}」のダウンロード中') 
                await fetch_single_embedded_image(tab, gen, normalized_url)
                append_to_job_log(f'押絵「{image_url}」をダウンロードしました')
    
    append_to_job_log(f'新たに発見された押絵のダウンロード完了')
    return image_hrefs_table