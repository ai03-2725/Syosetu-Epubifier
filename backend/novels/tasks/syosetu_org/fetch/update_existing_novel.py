# Fetch syosetu.org novels

import datetime
from pprint import pprint
from time import sleep
from django.conf import settings
from typing import NamedTuple, TypedDict

from django_rq import job
import asyncio
import django_rq
from pydoll.browser.chromium import Chrome
from rq.job import JobStatus


from novels.tasks.syosetu_org.fetch.fetch_embedded_images import fetch_embedded_images
from novels.tasks.syosetu_org.fetch.fetch_episode_contents import fetch_episode_contents
from novels.tasks.syosetu_org.fetch.fetch_novel_index_page import fetch_novel_index_page
from novels.tasks.syosetu_org.fetch.fetch_novel_details_page import fetch_novel_details_page
from novels.tasks.syosetu_org.process.generate_epub import generate_epub_syosetu_org
from novels.tasks.syosetu_org.types import DraftChapter, DraftEpisode
from novels.utils.append_to_job_log import append_to_job_log
from novels.utils.enqueue_generate_epub_with_metadata import enqueue_generate_epub_task
from novels.utils.get_children import get_chapters_of_novel_async, get_episodes_of_novel_async, get_episodes_of_novel_with_chapters_async
from novels.models import Novel, Chapter, Episode
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState
from url_normalize import url_normalize


@job
def update_existing_novel_syosetu_org(id: int, allow_delete: bool):
    """
    The job function run by the rqworker
    """
    changed = asyncio.run(_update_novel(id, allow_delete))
    return changed

    
async def _update_novel(id: int, allow_delete: bool):
    """
    The top level async function to update an existing novel
    """
    append_to_job_log(f"小説{str(id)}の更新を開始")
    
    # Keep track of the data already in the db
    # Default state for when the novel DNE
    db_novel = None
    db_chapters: list[Chapter] = []
    db_episodes: list[Episode] = []
    
    # The draft copies used for comparing and fetching
    
    # See if novel already exists
    try: 
        # Get the db novel
        db_novel = await Novel.objects.aget(source=url_normalize(f"https://syosetu.org/novel/{str(id)}/"))
        append_to_job_log(f"データベースから既存のデータを取得")
        novel_exists_in_db = True
        
        # If frozen, cancel fetch
        if db_novel.frozen:
            append_to_job_log(f"小説{str(id)}は凍結されてます")
            append_to_job_log(f"更新する場合は凍結を解除してください")
            return
        
        try:
            # Fetch corresponding chapters/episodes
            db_chapters = await get_chapters_of_novel_async(db_novel)
            db_episodes = await get_episodes_of_novel_with_chapters_async(db_novel)
        except Exception as e:
            append_to_job_log("エラー：データベースの章・話の取得に失敗")
            pprint(e)
            return
        
    except Novel.DoesNotExist:
        append_to_job_log(f"\nデータベースに存在しない小説です")
        return
    
    # Create browser instance
    options = ChromiumOptions()
    # options.page_load_state = PageLoadState.INTERACTIVE
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
    
    db_novel.last_fetch_timestamp = new_last_fetch_timestamp
    
    # Update the draft copy novel with newest info
    novel_details_changed = False
    if db_novel.title != novel_details.title:
       db_novel.title = novel_details.title
       novel_details_changed = True
    if db_novel.author != novel_details.author:
       db_novel.author = novel_details.author
       novel_details_changed = True
    if db_novel.status != novel_details.status:
        db_novel.status = novel_details.status
        novel_details_changed = True
    append_to_job_log(f"小説情報の更新完了")
    
    # Fetch novel index page to obtain a list of draft chapters
    try:
        (draft_chapters, draft_episodes) = await fetch_novel_index_page(tab, id)
    except:
        await browser.stop()
        raise
    
    # Update newest change timestamp on novel
    all_updated_timestamps = [e["last_updated"] for e in draft_episodes if e["last_updated"] is not None]
    # Just in case, handle the case in which there's 0 episodes (default to now())
    new_last_updated_timestamp = datetime.datetime.now()
    if len(all_updated_timestamps) > 0:
        new_last_updated_timestamp = max(all_updated_timestamps)
        append_to_job_log(f"最新更新日を検出：{new_last_updated_timestamp.strftime("%Y-%m-%d %H:%M")}")
    if db_novel.last_updated_timestamp != new_last_updated_timestamp:
        db_novel.last_updated_timestamp = new_last_updated_timestamp
        novel_details_changed = True
        
    
    # Check if any content updates are needed at all
    # First compare chapters
    chapters_pending_push: list[Chapter] = []
    deleted_chapters: list[Chapter] = []
    
    # Check for additions/changes
    for draft_chapter in draft_chapters:
        corresponding_db_chapter = next((c for c in db_chapters if c.chapter_number == draft_chapter["chapter_number"]), None)
        if corresponding_db_chapter is None:
            chapters_pending_push.append(Chapter(
                # Set novel right before push since it's still pending db changes
                chapter_number=draft_chapter["chapter_number"],
                chapter_title=draft_chapter["title"]
            ))
        elif corresponding_db_chapter.chapter_title != draft_chapter["title"]:
            corresponding_db_chapter.chapter_title = draft_chapter["title"]
            chapters_pending_push.append(corresponding_db_chapter)
            
    # Check for deletions
    for db_chapter in db_chapters:
        corresponding_draft_chapter = next((c for c in draft_chapters if c["chapter_number"] == db_chapter.chapter_number), None)
        if corresponding_draft_chapter is None:
            deleted_chapters.append(db_chapter)
    if len(deleted_chapters) > 0 and not allow_delete:
        append_to_job_log(f"以前取得した章が削除されました。（{str("、".join([c.chapter_title for c in deleted_chapters]))}）")
        append_to_job_log(f"もし削除しても良い場合は「削除モード」で更新を行ってください。")
        await browser.stop()
        return
    

    # Then check episodes for changes
    # Manage episodes as drafts since chapter objects still aren't pushed to db
    episodes_to_update: list[DraftEpisode] = [] 
    deleted_episodes: list[Episode] = []
    
    for draft_episode in draft_episodes:
        corresponding_db_episode = next((e for e in db_episodes if e.episode_number == draft_episode["episode_number"]), None)
        # Handle episode 0 separately since it's the overview page (doesn't have modifiedtimestamp)
        if draft_episode["episode_number"] == 0:
            if not corresponding_db_episode:
                raise Exception("存在するはずの話0番（あらすじページ）がデータベースに存在しません")
            elif corresponding_db_episode.contents != draft_episode["contents"]:
                episodes_to_update.append(draft_episode)
        # Handle normal episodes
        else:
            if corresponding_db_episode is None:
                episodes_to_update.append(draft_episode)
                append_to_job_log(f"{str(draft_episode['episode_number'])}話：新たに追加されました")
            elif draft_episode["title"] != corresponding_db_episode.episode_title:
                append_to_job_log(f"{str(draft_episode['episode_number'])}話：タイトルが更新されました（{corresponding_db_episode.episode_title} -> {draft_episode['title']}）")
                episodes_to_update.append(draft_episode)
            elif draft_episode["chapter_number"] != corresponding_db_episode.chapter.chapter_number:
                # Technically if just the chapter number changed, refetch isn't necessary
                # However if that large of a structural change occurred, may as well refetch just in case
                episodes_to_update.append(draft_episode)
                append_to_job_log(f"{str(draft_episode['episode_number'])}話：章が更新されました（{corresponding_db_episode.chapter.chapter_number} -> {draft_episode['chapter_number']}）")
            elif draft_episode["last_updated"] > corresponding_db_episode.last_known_update_timestamp:
                episodes_to_update.append(draft_episode)
                append_to_job_log(f"{str(draft_episode['episode_number'])}話：最新更新日が更新されました（{corresponding_db_episode.last_known_update_timestamp.isoformat()} -> {draft_episode['last_updated'].isoformat()}）")
    for db_episode in db_episodes:
        corresponding_draft_episode = next((e for e in draft_episodes if e["episode_number"] == db_episode.episode_number), None)
        if corresponding_draft_episode is None:
            deleted_episodes.append(db_episode)
    if len(deleted_chapters) > 0 and not allow_delete:
            append_to_job_log(f"以前取得した話が削除されました。（{str("、".join([e.episode_title for e in deleted_episodes]))}）")
            append_to_job_log(f"もし削除しても良い場合は「削除モード」で更新を行ってください。")
            await browser.stop()
            return
    
    # Skip refetching episode 0 since already fetched
    episodes_to_fetch = [e for e in episodes_to_update if e["episode_number"] != 0]
    
    # At this point, see if any episode refetching is even necessary
    if len(episodes_to_fetch) > 0:
        append_to_job_log(f"取得が必要な話を{len(episodes_to_fetch)}つ検出しました")
        # Fetch queued episodes
        try:
            episode_content_table = await fetch_episode_contents(tab, episodes_to_fetch)              
        except:
            await browser.stop()
            raise
        
        # Update draft episodes (in episodes_to_update) with fetched contents
        for ep_num, fetched_contents in episode_content_table.items():
            corresponding_draft_episode = next((e for e in episodes_to_update if e["episode_number"] == ep_num))
            corresponding_draft_episode["contents"] = fetched_contents
            
        # At this point, all content required to create/update the episodes resides in episodes_to_update
            
        # Fetch embedded images found in the modified episodes
        try:
            found_embedded_images = await fetch_embedded_images(tab, episodes_to_update)
        except:
            await browser.stop()
            raise
        # Leave the actual image URL swapping for later - store in original form to have the original copy, swap during epub conversion
    else:
        append_to_job_log(f"取得が必要な話はありません")
    
    
    # Push changes to the db
    # First push changes to the novel so that it can be renferenced by chapters as a foreign key
    await db_novel.asave()
    # Update the reference copy to reference as foreign key
    db_novel = await Novel.objects.aget(source=db_novel.source)
    append_to_job_log(f"データベースの小説データを更新しました")
    
    # Then handle chapters so that the episodes can reference them as foreign keys
    if len(chapters_pending_push) > 0 or len(deleted_chapters) > 0:
        for pending_chapter in chapters_pending_push:
            pending_chapter.novel = db_novel
            await pending_chapter.asave()
        for deleted_chapter in deleted_chapters:
            await deleted_chapter.adelete()
        append_to_job_log(f"データベースの章データ{len(chapters_pending_push) + len(deleted_chapters)}つを更新しました")
        # Refresh reference copy of db chapters for referencing from the pages
        db_chapters = await get_chapters_of_novel_async(db_novel)
    
    # Then create/modify the Episodes to push to the db based on the drafts in episodes_to_update
    episodes_pending_push: list[Episode] = []
    if len(episodes_to_update) > 0 or len(deleted_episodes) > 0:
        # Draft conversion
        for draft_episode in episodes_to_update:
            target_chapter = next((c for c in db_chapters if c.chapter_number == draft_episode["chapter_number"]))
            corresponding_db_episode = next((e for e in db_episodes if e.episode_number == draft_episode["episode_number"]), None)
            # If episode doesn't exist, create anew
            if corresponding_db_episode is None:
                episodes_pending_push.append(Episode(
                    chapter=target_chapter,
                    episode_number=draft_episode["episode_number"],
                    episode_title=draft_episode["title"],
                    last_known_update_timestamp=draft_episode["last_updated"],
                    contents=draft_episode["contents"]
                ))
            # Otherwise update the existing db entry
            else:
                corresponding_db_episode.chapter = target_chapter
                corresponding_db_episode.episode_title = draft_episode["title"]
                corresponding_db_episode.last_known_update_timestamp = draft_episode["last_updated"]
                corresponding_db_episode.contents = draft_episode["contents"]
                episodes_pending_push.append(corresponding_db_episode)
        # Then apply changes
        for pending_episode in episodes_pending_push:
            await pending_episode.asave()
        for deleted_episode in deleted_episodes:
            await deleted_episode.adelete()
        append_to_job_log(f"データベースの話データ{len(episodes_pending_push) + len(deleted_episodes)}つを更新しました")
        
    # Done    
    append_to_job_log(f"小説データ更新完了")
    await browser.stop()
    
    # If any changes occurred, enqueue an epub gneeration
    if novel_details_changed or len(chapters_pending_push) > 0 or len(episodes_pending_push) > 0 or len(deleted_chapters) > 0 or len(deleted_episodes) > 0:
        enqueue_generate_epub_task(db_novel.id)
        
        
        
    return 
    


    

            
            
            
                
    
        
