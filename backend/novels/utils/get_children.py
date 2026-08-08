

from novels.models import Novel, Chapter, Episode


def get_chapters_of_novel(novel: Novel) -> list[Chapter]:
    chapters = list(Chapter.objects.order_by("chapter_number").filter(novel__id=novel.id))
    return chapters

async def get_chapters_of_novel_async(novel: Novel) -> list[Chapter]:
    chapters = [c async for c in Chapter.objects.order_by("chapter_number").filter(novel__id=novel.id)]
    return chapters
    
def get_episodes_of_chapter(chapter: Chapter) -> list[Episode]:
    episodes = list(Episode.objects.order_by("episode_number").filter(chapter__id=chapter.id))
    return episodes

async def get_episodes_of_chapter_async(chapter: Chapter) -> list[Episode]:
    episodes = [e async for e in Episode.objects.order_by("episode_number").filter(chapter__id=chapter.id)]
    return episodes

def get_episodes_of_novel(novel: Novel) -> list[Episode]:
    episodes = list(Episode.objects.order_by("episode_number").filter(chapter__novel__id=novel.id))
    return episodes

async def get_episodes_of_novel_async(novel: Novel) -> list[Episode]:
    episodes = [e async for e in Episode.objects.order_by("episode_number").filter(chapter__novel__id=novel.id)]
    return episodes

async def get_episodes_of_novel_with_chapters_async(novel: Novel) -> list[Episode]:
    episodes = [e async for e in Episode.objects.order_by("episode_number").select_related("chapter").filter(chapter__novel__id=novel.id)]
    return episodes


