# Fetch syosetu.org novel anew

import datetime
from time import sleep

from django_rq import job
import asyncio
import django_rq
from pydoll.browser.chromium import Chrome
from django.conf import settings
from rq.job import JobStatus


from novels.tasks.syosetu_org.fetch.fetch_embedded_images import fetch_embedded_images
from novels.tasks.syosetu_org.fetch.fetch_episode_contents import fetch_episode_contents
from novels.tasks.syosetu_org.fetch.fetch_novel_index_page import fetch_novel_index_page
from novels.tasks.syosetu_org.fetch.fetch_novel_details_page import fetch_novel_details_page
from novels.tasks.syosetu_org.process.generate_epub import generate_epub_syosetu_org
from novels.utils.append_to_job_log import append_to_job_log
from novels.utils.get_children import get_chapters_of_novel_async
from novels.models import Novel, Chapter, Episode
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState
from url_normalize import url_normalize


@job
def fetch_new_novel_syosetu_org(id: int):
    """
    The job function run by the rqworker
    """
    changed = asyncio.run(_fetch_new_novel(id))
    return changed


async def _fetch_new_novel(id: int):
    """
    The top level async function to fetch a whole novel anew
    """
    
    # See if novel already exists
    # If it does, cancel fetch
    try: 
        db_novel = await Novel.objects.aget(source=url_normalize(f"https://syosetu.org/novel/{str(id)}/"))
        append_to_job_log("既にこの小説は登録されています")
        raise Exception("Duplicate novel object")
        
    except Novel.DoesNotExist:
        append_to_job_log(f"小説{str(id)}の新規取得を開始")
        pass
    
    db_novel = Novel(
        frozen=False
    )
        
    # Create browser instance
    options = ChromiumOptions()
    options.page_load_state = PageLoadState.COMPLETE
    if settings.PYDOLL_USE_CHROMIUM:
        options.binary_location = '/usr/bin/chromium'
    browser = Chrome(options=options)
    # Start a new browser tab
    tab = await browser.start()
    
    # Fetch novel details 
    new_last_fetch_timestamp = datetime.datetime.now()
    try:
        novel_details = await fetch_novel_details_page(tab, id)
    except:
        await browser.stop()
        raise
    
    # Update the draft copy novel with newest info
    db_novel.title = novel_details.title
    db_novel.author = novel_details.author
    db_novel.source = url_normalize(f"https://syosetu.org/novel/{str(id)}/")
    db_novel.status = novel_details.status
    db_novel.last_fetch_timestamp = new_last_fetch_timestamp
    append_to_job_log(f"小説情報の取得完了")
    
    # Fetch novel index page to obtain a list of draft chapters
    try:
        (draft_chapters, draft_episodes) = await fetch_novel_index_page(tab, id)
    except:
        await browser.stop()
        raise
    
    # Obtain last updated timestamp
    # First build a list of all timestamps from all episodes
    all_updated_timestamps = [e["last_updated"] for e in draft_episodes if e["last_updated"] is not None]
    # Just in case, handle the case in which there's 0 episodes (default to now())
    new_last_updated_timestamp = datetime.datetime.now()
    if len(all_updated_timestamps) > 0:
        new_last_updated_timestamp = max(all_updated_timestamps)
        append_to_job_log(f"最新更新日を検出：{new_last_updated_timestamp.strftime("%Y-%m-%d %H:%M")}")
    db_novel.last_updated_timestamp = new_last_updated_timestamp
    
    # Build a list of chapters/episodes which need to be created into the db
    chapters_to_push: list[Chapter] = []
    
    # Create chapter entries for the pending db list
    for draft_chapter in draft_chapters:
        chapters_to_push.append(Chapter(
            novel=db_novel,
            chapter_number=draft_chapter["chapter_number"],
            chapter_title=draft_chapter["title"]
        ))
    append_to_job_log(f"章を{len(chapters_to_push)}つ検出しました")
    
    # NOTE: Uncomment below to limit everything to just two episodes (overview + first text content) for fast debugging
    # draft_episodes = draft_episodes[:2]
    
    # Fetch all episodes except episode 0 (which is the overview with text content pre-fetched from the index page)
    try:
        episode_content_table = await fetch_episode_contents(tab, draft_episodes[1:])
    except:
        await browser.stop()
        raise
    
    # Update draft episodes with fetched contents
    for ep_num, fetched_contents in episode_content_table.items():
        corresponding_draft_episode = next((e for e in draft_episodes if e["episode_number"] == ep_num))
        corresponding_draft_episode["contents"] = fetched_contents
        
    # Fetch embedded images found in the provided draft episodes
    try:
        found_embedded_images = await fetch_embedded_images(tab, draft_episodes)
    except:
        await browser.stop()
        raise
    # Leave the actual image URL swapping for later - store in original form to have the original copy, swap during epub conversion
    
    
    # Push changes to the db
    # First push changes to the novel so that it can be renferenced by chapters as a foreign key
    await db_novel.asave()
    # Update the reference copy to reference as foreign key
    db_novel = await Novel.objects.aget(source=db_novel.source)
    append_to_job_log(f"データベースの小説データを保存しました")
    
    # Then handle chapters so that the episodes can reference them as foreign keys
    for pending_chapter in chapters_to_push:
        pending_chapter.novel = db_novel
        await pending_chapter.asave()
    append_to_job_log(f"データベースの章データ{len(chapters_to_push)}つを保存しました")
    # Refresh reference copy of db chapters for referencing from the pages
    db_chapters = await get_chapters_of_novel_async(db_novel)
    
    # Then create all episodes
    for draft_episode in draft_episodes:
        target_chapter = next((c for c in db_chapters if c.chapter_number == draft_episode["chapter_number"]))
        await Episode(
            chapter=target_chapter,
            episode_number=draft_episode["episode_number"],
            episode_title=draft_episode["title"],
            last_known_update_timestamp=draft_episode["last_updated"],
            contents=draft_episode["contents"]
        ).asave()
    append_to_job_log(f"データベースの話データ{len(draft_episodes)}つを保存しました")
        
    # Done    
    append_to_job_log(f"小説データ保存完了")
    await browser.stop()
    
    # Enqueue an epub gneeration
    enqueued_task = django_rq.enqueue(generate_epub_syosetu_org, db_novel.id, result_ttl=43200)
        
    return 
    
