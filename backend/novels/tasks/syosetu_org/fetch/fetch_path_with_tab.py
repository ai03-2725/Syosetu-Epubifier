import time

from pydoll.browser.tab import Tab
from pydoll.protocol.fetch.events import FetchEvent, RequestPausedEvent
from pydoll.protocol.network.types import ErrorReason

from novels.utils.append_to_job_log import append_to_job_log

# Blocked URL path bits to speed up loading

BLOCKED_URL_CONTENTS: list[str] = [
    "geniee.jp",
    "doubleclick.net",
    "yads.c.yimg.jp",
    "adrecover.com",
    "https://cs.syosetu.org/ad",
    "dlsite.jp",
    "google.co.jp/ads/",
    "ad_dliste.min.js",
    "indexww.com",
    "criteo.com",
    "im-apps.net",
]

async def fetch_path_with_tab(path: str, tab: Tab):
    """
    Load a path under syosetu.org using the tab object
    Handles unnecessary element blocking and similar
    """
    append_to_job_log(f"URL「{path}」を取得中")
    
    # Load novel details page
    async def handle_request(event: RequestPausedEvent):
        request_id = event['params']['requestId']
        url = event['params']['request']['url']

        if any(blocked_domain for blocked_domain in BLOCKED_URL_CONTENTS if (blocked_domain in url)):
            # Block unnecessary content to speed up load
            # print(f"Blocked URL: '{url}'")
            await tab.fail_request(request_id, ErrorReason.BLOCKED_BY_CLIENT)
            
        else:
            # Continue the request without modifications
            # print(f"Allowing URL: '{url}")
            await tab.continue_request(request_id)
    
    await tab.enable_fetch_events()
    # Record starting timestamp
    start_time = time.time()
    await tab.on(FetchEvent.REQUEST_PAUSED, handle_request)
    async with tab.expect_and_bypass_cloudflare_captcha():
        await tab.go_to(path)
    await tab.disable_fetch_events()
    # Check ending timestamp
    elapsed_time = time.time() - start_time
    # If elapsed time is less than 4 seconds, wait at least 4 seconds to reduce excess strain on servers
    # Should never be the case since the pages include a loadAd() timeout which takes 6 seconds anyways
    if elapsed_time < 4:
        await time.sleep(4 - elapsed_time)
    # Return back to caller with tab contents loaded
    append_to_job_log(f"URL「{path}」の取得完了")