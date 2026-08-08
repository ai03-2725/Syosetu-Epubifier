import base64
import time

from snowflake.snowflake import SnowflakeGenerator
from url_normalize import url_normalize
from pydoll.browser.tab import Tab
from django.core.files.base import ContentFile

from novels.models import UploadedImage
from novels.utils.append_to_job_log import append_to_job_log
    
    
async def fetch_single_embedded_image(tab: Tab, gen: SnowflakeGenerator, image_url: str):
    normalized_url = url_normalize(image_url)
    
    append_to_job_log(f'押絵へアクセス中')
    
    await tab.enable_network_events()
    # await tab.on(FetchEvent.REQUEST_PAUSED, intercept_image)
    start_time = time.time()
    async with tab.expect_and_bypass_cloudflare_captcha():
        await tab.go_to(normalized_url)
    append_to_job_log(f'押絵へのアクセス完了')
    elapsed_time = time.time() - start_time
    # If elapsed time is less than 4 seconds, wait at least 4 seconds to reduce excess strain on servers
    if elapsed_time < 4:
        await time.sleep(4 - elapsed_time)
    
    logs = await tab.get_network_logs()
    append_to_job_log(f'押絵のネットワークアクセスログをスキャン中')
    
    # Scan logs for resource request whose URL is the image URL itself
    for log in logs:
        url = log.get('params', {}).get('request', {}).get('url')
        if url is None:
            continue
        
        # Look for a perfect match to the image file URL provided
        if url_normalize(url) == url_normalize(image_url.lower()):
            append_to_job_log(f'押絵のデータを検出')
            request_id = log['params']['requestId']
            
            # Obtain its image body data directly
            image_body = await tab.get_network_response_body(request_id)
            
            # Decode the b64 encoded data 
            decoded_image = base64.b64decode(image_body)
            
            # Generate a filename
            filename = str(next(gen)) + '.' + normalized_url.split('.')[-1].replace('/', '')
            append_to_job_log(f'ファイル名「{filename}」として保存中')
            # Create the file object in the db
            new_image = UploadedImage(
                source_src=normalized_url,
                image_file=ContentFile(decoded_image, filename)
            )
            await new_image.asave()
            await tab.disable_network_events()
            return new_image
    
    await tab.disable_network_events()
    raise Exception("intercept_image: 画像データがみつかりませんでした")