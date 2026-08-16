from bs4 import BeautifulSoup
from snowflake.snowflake import SnowflakeGenerator

from novels.models import UploadedImage
from novels.tasks.syosetu_org.fetch.fetch_embedded_images import fetch_single_embedded_image
from novels.tasks.syosetu_org.process.find_embedded_images import find_embedded_images


import datetime

from pydoll.browser.chromium import Chrome

from novels.tasks.syosetu_org.fetch.fetch_novel_details_page import fetch_novel_details_page
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

from novels.utils.append_to_job_log import append_to_job_log


async def replace_image_urls(soup: BeautifulSoup) -> list[UploadedImage] | None:
    """
    Replace embedded image links (links marked 押絵) with img tags within the provided BS4 object for embedding images directly into the epub pages
    Returns a list of UploadedImages involved if any image links were swapped, or None if unchanged
    """
    
    # Get list of embedded images
    urls_list = find_embedded_images(soup)
    if len(urls_list) == 0:
        # append_to_job_log("置き換える画像タグはありません")
        return None
    
    # If images exist, look up each in the db
    # All should exist given that they're fetched along with the novel
    # append_to_job_log("置き換える画像タグを発見しました")
    
    involved_images: list[UploadedImage] = []
    
    for image_url in urls_list:
        try:
            db_image = await UploadedImage.objects.aget(source_src = image_url)
        except UploadedImage.DoesNotExist:
            # This shouldn't happen since novel images are fetched at fetch-time
            raise Exception("replace_image_urls: データベースに画像ファイルが存在しません")
            
        filename = db_image.image_file.name
        new_path = "Images/" + filename # Images should be copied to the Images/ directory within the epub
        a_tags = soup.find_all(lambda t: t.name == 'a' and t.get('href') == image_url)
        for a_tag in a_tags:
            new_tag = soup.new_tag("img")
            new_tag["src"] = new_path
            a_tag.replace_with(new_tag)
        involved_images.append(db_image)
    
    # append_to_job_log(f"画像リンクを入れ替えました")
    return involved_images