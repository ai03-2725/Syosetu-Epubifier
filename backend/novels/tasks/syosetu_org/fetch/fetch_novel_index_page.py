import datetime
from typing import cast

from bs4 import BeautifulSoup
from pydoll.browser.tab import Tab
from novels.tasks.syosetu_org.types import DraftChapter, DraftEpisode
from novels.utils.append_to_job_log import append_to_job_log
from novels.tasks.syosetu_org.fetch.fetch_path_with_tab import fetch_path_with_tab

async def fetch_novel_index_page(tab: Tab, id: int) -> tuple[list[DraftChapter], list[DraftEpisode]]:
    """
    Fetches novel index page (i.e. the one with all the chapters listed)
    Returns a tuple of (title, author, tags, Chapters, Episodes)
    """
    
    # Create working copy of found chapters/episodes to build and return
    draft_chapters: list[DraftChapter] = []
    draft_episodes: list[DraftEpisode] = []
    
    # Load novel index page
    append_to_job_log(f"小説の目次を取得中")
    await fetch_path_with_tab(f'https://syosetu.org/novel/{str(id)}/', tab)
    html_content = await tab.page_source
    
    # Parse using BS4 for higher reliability and simplicity
    soup = BeautifulSoup(html_content, 'html.parser')    
    
    # Get index page contents
    # Structure: Updated 2026-07-31
    # First div occurrence with class "ss" -> 
    #   - Span with attr itemprop="name" = Title
    #   - Div -> loose text "作者：" and span with attr itemprop="author" with author name inside
    #   - Span with attr itemprop="genre" = Derivative source (原作： or オリジナル：)
    #   - Loose text "タグ：" is followed by a mix of <a>s and <span>s at the same level for tags (look until a br which separates taglist from an a with text "▼下部メニューに飛ぶ")
    # 
    # Second div occurrence with class "ss" -> contents = Novel overview text
    # Ul with class "episode-list__items" = list of contents; children are either
    #   - Li of class "episode-list__item" -> a = Episode
    #     - href attribute = Episode URL + Chapter id (i.e. "./1.html")
    #       - Span with class "episode-list__title" = Episode title
    #       - Time with class "episode-list__date" = Episode publish date (inner text of format "2026/05/24 18:00")
    #       - Span with class "episode-list__revision" = Episode last modified date (attribute title -> "2026/07/26 16:16改稿" if any updates exist, attr doesn't exist otherwise (but empty tag still exists)) 
    #   - Li of class "episode-list__chapter" -> div of class "episode-list__chapter-title" = Chapter
    #     - inner text of div is chapter title
    
    ss_divs = soup.find_all('div', class_="ss")
    
    # Get title/author/etc out of first ss div
    details_div = ss_divs[0]
    title_text = details_div.find('span', attrs={"itemprop": "title"}).get_text(strip=True)
    author_text = details_div.find('span', attrs={"itemprop": "author"}).get_text(strip=True)
    genre_text = details_div.find('span', attrs={"itemprop": "genre"}).get_text(strip=True)
    # Iterate over tag tags
    tags_list = [ genre_text ]
    current_tag_node = details_div.find(string="タグ：")
    while True:
        current_tag_node = current_tag_node.find_next()
        if current_tag_node.name == "a" or current_tag_node.name == "span":
            tags_list.append(current_tag_node.get_text(strip=True))
        else:
            break
    
    # Get overview text from second ss div
    overview_div = ss_divs[1] # Overview is stored in the second div with class "ss"
    overview_raw = overview_div.decode_contents() # Obtain inner HTML as string
    overview = overview_raw.removesuffix('<hr style="margin:20px 0px;">') # Clear out trailing hr
    # Add novel URL to overview text for parity with narou.rb format
    overview += f'<p><br/></p><p>掲載ページ:</p><p><a href="https://syosetu.org/novel/{str(id)}/">https://syosetu.org/novel/{str(id)}/</a></p>'
    
    contents_list = soup.find('ul', class_="episode-list__items") 
    
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
    
    # Parse ToC
    # First get all direct child li elements under the contents_list ul
    for content_item in contents_list.find_all(recursive=False):
        
        content_item_classes = content_item.get('class', [])
        
        # Handle episodes
        if "episode-list__item" in content_item_classes:
            
            draft_episode = DraftEpisode()
            
            # Direct child is an a-tag wrapper around everything else
            # Extract it and its href tag to get its episode number
            a_wrapper = content_item.find('a')
            a_href = a_wrapper['href']
            episode_number = int(a_href.removeprefix("./").removesuffix(".html"))
            draft_episode["episode_number"] = episode_number
            draft_episode["href"] = f"https://syosetu.org/novel/{str(id)}/{a_href.removeprefix("./")}"
            
            # Track last updated date
            last_known_change_datetime = datetime.datetime.fromisoformat("1970-01-01")
            
            # Check children of a-wrapper to obtain episode details
            for a_child in a_wrapper.find_all(recursive=False):
                
                a_child_classes = a_child.get('class', [])
                
                # Handle episode title
                if "episode-list__title" in a_child_classes:
                    draft_episode['title'] = a_child.get_text()
                
                # Handle episode publish date
                elif "episode-list__date" in a_child_classes:
                    publish_date_str = a_child.get_text()
                    publish_date = datetime.datetime.strptime(publish_date_str, '%Y/%m/%d %H:%M')
                    if publish_date > last_known_change_datetime:
                        last_known_change_datetime = publish_date
                        
                # Handle episode update date
                elif "episode-list__revision" in a_child_classes:
                    update_date_title_attr = a_child.get('title')
                    if update_date_title_attr is not None:
                        update_date = datetime.datetime.strptime(update_date_title_attr, '%Y/%m/%d %H:%M改稿')
                        if update_date > last_known_change_datetime:
                            last_known_change_datetime = update_date
                
                # Skip anything else
                else:
                    pass
            
            # Children checking complete
            # Set the last known update date 
            draft_episode["last_updated"] = last_known_change_datetime
                        
            # Mark contents as none = to fetch afterwards if needed
            draft_episode["contents"] = None
            
            # Set the episode's chapter ID to the latest known chapter 
            draft_episode["chapter_number"] = draft_chapters[-1]["chapter_number"]
            
            # Add episode to latest chapter
            draft_episodes.append(draft_episode)
            
        # Handle chapters
        elif "episode-list__chapter" in content_item_classes:
            
            draft_chapter = DraftChapter()
            
            # Extract title string
            title_string = content_item.get_text()
            draft_chapter["title"] = title_string
                        
            # Insert chapter at the next available ID
            draft_chapter["chapter_number"] = len(draft_chapters)
            draft_chapters.append(draft_chapter)
            
            
    # Finished checking table of contents
    # Return found chapters and episodes
    append_to_job_log(f"目次の取得が完了 - 全{len(draft_episodes) - 1}話") # Account for the added overview page
    return (title_text, author_text, tags_list, draft_chapters, draft_episodes)
            



