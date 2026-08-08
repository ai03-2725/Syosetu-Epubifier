
from pprint import pprint

from pydoll.browser.tab import Tab
from novels.tasks.syosetu_org.types import DraftEpisode
from novels.utils.append_to_job_log import append_to_job_log
from novels.tasks.syosetu_org.fetch.fetch_path_with_tab import fetch_path_with_tab

async def fetch_episode_contents(tab: Tab, episodes: list[DraftEpisode]) -> dict[int, str]:
    """
    Fetches given episodes 
    If a href is defined and contents = None, fetches the contents from the web
    Returns a dict of {episode_number: "contents", ...}
    """
    
    fetched_episodes: dict[int, str] = {}
    
    for index, episode in enumerate(episodes):
        
        # If the episode link is None or if the contents are already defined, skip fetching
        # TODO: For now this should never happen - raise if true
        if episode["href"] is None or episode["contents"] is not None:
            append_to_job_log(f'（{str(index + 1)}/{str(len(episodes))}）{str(episode["episode_number"])}話「{episode["title"]}」は内容が既に存在します')
            pprint(episode)
            raise
        
        # Otherwise fetch
        else:
            
            # Update job status to reflect progress
            append_to_job_log(f'（{str(index + 1)}/{str(len(episodes))}）{str(episode["episode_number"])}話「{episode["title"]}」の内容をダウンロード中・・・')
                
            await fetch_path_with_tab(episode["href"], tab)
            # Content blocks:
            # <div id="maegaki"> -> Maegaki
            # <div id="honbun"> -> Main
            # <div id="atogaki"> -> Atogaki
            # Maegaki/Atogaki is optional - may as well treat all blocks as possibly nonexistent
            
            contents: str = ""
            
            div_maegaki = await tab.query("//div[@id='maegaki']", raise_exc=False)
            div_honbun = await tab.query("//div[@id='honbun']", raise_exc=False)
            div_atogaki = await tab.query("//div[@id='atogaki']", raise_exc=False)
            
            # Honbun/main text is properly tagged with all lines wrapped in <p>
            # Maegaki/Atogaki is simply text dumped into a div with no p wrapper; keep the outer wrapper div to keep things discernable/post-processable
            if div_maegaki is not None:
                # contents += ((await div_maegaki.inner_html).removeprefix('<div id="maegaki">')).removesuffix('</div>')
                contents += (await div_maegaki.inner_html)
            if div_honbun is not None:
                contents += ((await div_honbun.inner_html).removeprefix('<div id="honbun">')).removesuffix('</div>')  
            if div_atogaki is not None:
                # contents += ((await div_atogaki.inner_html).removeprefix('<div id="atogaki">')).removesuffix('</div>')
                contents += (await div_atogaki.inner_html)
            
            # Add fetched contents to lookup table
            fetched_episodes[episode["episode_number"]] = contents
            append_to_job_log(f'{str(episode["episode_number"])}話の内容ダウンロード完了')
    
    append_to_job_log(f"合計{len(episodes)}話分の内容を取得しました")
    return fetched_episodes
            