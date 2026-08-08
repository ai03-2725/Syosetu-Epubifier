


import asyncio
import io
import mimetypes
from django.conf import settings

from django_rq import job
from ebooklib import epub
from pathvalidate import sanitize_filename
from url_normalize import url_normalize

from novels.models import EpubFile, Novel
from novels.tasks.syosetu_org.process.cleanup_html import cleanup_html
from novels.tasks.syosetu_org.process.prettify_html import prettify_html
from novels.tasks.syosetu_org.process.replace_image_urls import replace_image_urls
from novels.tasks.syosetu_org.process.source_to_id import source_to_id
from novels.utils.append_to_job_log import append_to_job_log
from novels.utils.get_children import get_chapters_of_novel_async, get_episodes_of_novel_with_chapters_async
from django.core.files.base import ContentFile


@job
def generate_epub_syosetu_org(novel_id: int):
    """
    The job function run by the rqworker
    """
    asyncio.run(_generate_epub(novel_id))
    return

async def _generate_epub(novel_id: int):
    
    db_novel = await Novel.objects.aget(id=novel_id)
    syosetu_id = source_to_id(db_novel.source)
    
    book = epub.EpubBook()
    
    db_episodes = await get_episodes_of_novel_with_chapters_async(db_novel)
    db_chapters = await get_chapters_of_novel_async(db_novel)

    # Set metadata
    book.set_identifier(f"SyosetuEpubifier-syosetu_org-{syosetu_id}")
    book.set_title(db_novel.title)
    book.set_language("ja")
    book.add_author(db_novel.author)
    book.add_metadata("DC", "date", db_novel.last_updated_timestamp.strftime("%Y-%m-%d"))
    book.add_metadata("DC", "publisher", "Web小説投稿サイト ハーメルン (https://syosetu.org/)")
    book.add_metadata(None, "novel_source", db_novel.source)
    book.add_metadata(None, "generated_by", "Syosetu-Epubifier")
    book.add_metadata(None, "last_fetch_date", db_novel.last_fetch_timestamp.strftime("%Y-%m-%d"))
    book.spine = ['nav']
    
    # Load and add stylesheets
    default_css_path = settings.BASE_DIR / 'novels' / 'templates' / 'default_css.css'
    default_css = ""
    with open(default_css_path, "r", encoding="utf-8") as default_css_file:
        default_css = default_css_file.read()
    default_css_epubitem = epub.EpubItem(
        uid="style_default", file_name="Styles/default.css", media_type="text/css", content=default_css
    )
    book.add_item(default_css_epubitem)
    
    # Track chapters/episodes for conversion to ToC
    # toc_lookup_table[chapter_num] = [episodes...]
    # Chapter 0 = the base chapter that doesn't have any nesting (novel overview, uncategorized episodes)
    # Chapter 1 onwards = nest its episodes below
    toc_lookup_table: dict[int, list[epub.EpubHtml]] = {}
    
    # Convert episodes
    for episode in db_episodes:
        
        # Add the content itself
        ebook_episode = epub.EpubHtml(title=episode.episode_title, file_name=f"{episode.episode_number:04d}.xhtml", lang="ja")
        ebook_episode.add_item(default_css_epubitem)
        book.add_item(ebook_episode)
        
        # Add title heading to beginning of episode
        prefixed_contents = episode.contents
        prefixed_contents = f'<h2>{episode.episode_title}</h2></div><p><br/></p><p><br/></p>' + prefixed_contents
        if episode.chapter.chapter_number > 0:
            prefixed_contents = f'<small>{episode.chapter.chapter_title}</small>' + prefixed_contents
            
        # Cleanup the raw content HTML
        cleaned_html = cleanup_html(prefixed_contents)
        append_to_job_log(f"{str(episode.episode_number)}話の内容を確認中")
        
        # Handle embedded images
        embedded_images = await replace_image_urls(cleaned_html)
        if embedded_images is not None:
            new_content, involved_images = embedded_images
            ebook_episode.content = prettify_html(new_content)
            for image in involved_images:
                image_content = image.image_file.open('rb').read()
                media_type, _ = mimetypes.guess_type(image.image_file.path)
                ebook_image = epub.EpubImage(uid=f"image_{image.image_file.name}", file_name=f"Images/{image.image_file.name}", content=image_content, media_type=media_type) 
                book.add_item(ebook_image)
        else:
            ebook_episode.content = prettify_html(cleaned_html)
            
        # Add episode to spine
        book.spine.append(ebook_episode)
        
        # Add episode to toc lookup table
        # Initialize array if first time finding an episode from the chapter
        if episode.chapter.chapter_number not in toc_lookup_table:
            toc_lookup_table[episode.chapter.chapter_number] = []
        # Then append
        toc_lookup_table[episode.chapter.chapter_number].append(ebook_episode)
            
    # Convert ToC lookup table into actual ToC
    # Start with chapter 0 (uncategorized) - specify by number just in case negative indices get added in the future
    toc_draft = []
    toc_draft.extend(toc_lookup_table.pop(0, []))
    for chapter_num, ebook_episodes in toc_lookup_table.items():
        db_chapter = next((c for c in db_chapters if c.chapter_number == chapter_num))
        toc_draft.append((epub.Section(db_chapter.chapter_title), tuple(ebook_episodes)))
    book.toc = tuple(toc_draft)
    
    # Style the nav page
    # TODO: For now reusing the basic style
    nav_css = epub.EpubItem(uid="style_nav", file_name="Styles/nav.css", media_type="text/css", content=default_css)
    book.add_item(nav_css)
    
    # Add required navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Generate the book file data
    buffer = io.BytesIO()
    epub.write_epub(buffer, book)
    file_bytes = buffer.getvalue()
    
    # Delete old file if exists
    try:
        old_epub = await EpubFile.objects.aget(novel=db_novel)
        old_epub.file.delete()
        old_epub.adelete()
    except:
        pass
    
    generated_epub = EpubFile(
        novel=db_novel,
        file=ContentFile(file_bytes, sanitize_filename(f"syosetu_org-{str(source_to_id(db_novel.source))}-{db_novel.title}.epub"))
    )
    await generated_epub.asave()

    
    
    
    
            
        
        
    