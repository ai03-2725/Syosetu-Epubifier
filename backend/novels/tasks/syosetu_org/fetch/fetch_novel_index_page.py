import datetime

from pydoll.browser.tab import Tab
from novels.tasks.syosetu_org.types import DraftChapter, DraftEpisode
from novels.utils.append_to_job_log import append_to_job_log
from novels.tasks.syosetu_org.fetch.fetch_path_with_tab import fetch_path_with_tab

async def fetch_novel_index_page(tab: Tab, id: int) -> tuple[list[DraftChapter], list[DraftEpisode]]:
    """
    Fetches novel index page (i.e. the one with all the chapters listed)
    Returns a list of Chapters and Episodes
    """
    
    # Create working copy of found chapters/episodes to build and return
    draft_chapters: list[DraftChapter] = []
    draft_episodes: list[DraftEpisode] = []
    
    # Load novel index page
    append_to_job_log(f"小説の目次を取得中")
    await fetch_path_with_tab(f'https://syosetu.org/novel/{str(id)}/', tab)
        
    
    # Get index page contents
    # Structure: Updated 2026-07-31
    # Second div occurrence with class "ss" -> contents = Novel overview text
    # Ul with class "episode-list__items" = list of contents; children are either
    #   - Li of class "episode-list__item" -> a = Episode
    #     - href attribute = Episode URL + Chapter id (i.e. "./1.html")
    #     - child Span with class "episode-list__title" = Episode title
    #     - child Time with class "episode-list__date" = Episode publish date (inner text of format "2026/05/24 18:00")
    #     - child Span with class "episode-list__revision" = Episode last modified date (attribute title -> "2026/07/26 16:16改稿" if any updates exist, attr doesn't exist otherwise (but empty tag still exists)) 
    #   - Li of class "episode-list__chapter" -> div of class "episode-list__chapter-title" = Chapter
    #     - inner text of div is chapter title
    
    overview_raw = await (await tab.query("//div[@class='ss'][2]")).inner_html
    overview = overview_raw.removesuffix('<hr style="margin:20px 0px;"></div>').removeprefix('<div class="ss">')
    # Add novel URL to overview text for parity with narou.rb format
    overview += f'<p><br/></p><p>掲載ページ:</p><p><a href="https://syosetu.org/novel/{str(id)}/">https://syosetu.org/novel/{str(id)}/</a></p>'
    
    contents_list = await tab.query("//ul[@class='episode-list__items']")
    content_items = await contents_list.get_children_elements(max_depth=1)
    
    # Create 0th starting chapter which includes the overview text episode
    draft_chapters.append(DraftChapter(
        chapter_number=0, 
        title="", # Blank - inherit book title for the first sections
    ))
    
    # Add overview page as 0th episode
    draft_episodes.append(DraftEpisode(
        episode_number=0, 
        chapter_number=0, 
        title="あらすじ", 
        last_updated=None, 
        href=None,
        contents=overview,
    ))
    
    # Parse table of contents
    for content_item in content_items:
        
        # Handle episodes
        if "episode-list__item" in content_item.class_name:
            
            draft_episode = DraftEpisode()
            
            # Find child a element and obtain episode path + number
            a_element = (await content_item.get_children_elements(max_depth=1, tag_filter=["a"]))[0]
            a_href = a_element.get_attribute("href")
            episode_number = int(a_href.removeprefix("./").removesuffix(".html"))
            draft_episode["episode_number"] = episode_number
            draft_episode["href"] = f"https://syosetu.org/novel/{str(id)}/{a_href.removeprefix("./")}"
            
            # Keep track of known last updated date
            last_known_change_datetime = datetime.datetime.fromisoformat("1970-01-01")
            
            # Query its children to fetch details of the episode
            a_children = await a_element.get_children_elements(max_depth=1)
            for a_child in a_children:
                # Handle episode title
                if "episode-list__title" in a_child.class_name:
                    draft_episode["title"] = await a_child.text
                # Handle episode publish date
                elif "episode-list__date" in a_child.class_name:
                    publish_date_str = await a_child.text
                    publish_date = datetime.datetime.strptime(publish_date_str, '%Y/%m/%d %H:%M')
                    if publish_date > last_known_change_datetime:
                        last_known_change_datetime = publish_date
                # Handle episode update date
                elif "episode-list__revision" in a_child.class_name:
                    update_date_title_attr = a_child.get_attribute("title")
                    if update_date_title_attr is not None:
                        update_date = datetime.datetime.strptime(update_date_title_attr, '%Y/%m/%d %H:%M改稿')
                        if update_date > last_known_change_datetime:
                            last_known_change_datetime = update_date
                # Skip anything else
                else:
                    pass
                
            # Set the last known update date 
            draft_episode["last_updated"] = last_known_change_datetime
            
            # Mark contents as none = to fetch afterwards if needed
            draft_episode["contents"] = None
            
            # Set the episode's chapter ID to the latest known chapter 
            draft_episode["chapter_number"] = draft_chapters[-1]["chapter_number"]
            
            # Add episode to latest chapter
            draft_episodes.append(draft_episode)
        
        # Handle chapters
        elif "episode-list__chapter" in content_item.class_name:
            
            draft_chapter = DraftChapter()
            
            # Get child div to fetch title
            div_elements = await content_item.get_children_elements(max_depth=1, tag_filter=["div"])
            div_element = next(obj for obj in div_elements if "episode-list__chapter-title" in obj.class_name)
            title_string = await div_element.text
            
            draft_chapter["title"] = title_string
            
            # Insert chapter at the next available ID
            draft_chapter["chapter_number"] = len(draft_chapters)
            draft_chapters.append(draft_chapter)
            
    # Finished checking table of contents
    # Return found chapters and episodes
    append_to_job_log(f"目次の取得が完了 - 全{len(draft_episodes) - 1}話") # Account for the added overview page
    return (draft_chapters, draft_episodes)
            



