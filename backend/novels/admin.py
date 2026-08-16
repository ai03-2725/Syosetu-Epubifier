from django.contrib import admin

from novels.models import Chapter, Episode, Novel, UploadedImage, EpubFile

# Register your models here.
@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'last_fetch_timestamp', 'last_updated_timestamp')

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('get_novel_title', 'chapter_number', 'chapter_title')
    def get_novel_title(self, obj):
        return obj.novel.title
    
@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('get_novel_title', 'get_chapter_title', 'episode_number', 'episode_title')
    def get_novel_title(self, obj):
        return obj.chapter.novel.title
    def get_chapter_title(self, obj):
        return obj.chapter.chapter_title
    
@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ('source_src', 'get_filename')
    def get_filename(self, obj):
        return obj.image_file.path

@admin.register(EpubFile)
class EpubFileAdmin(admin.ModelAdmin):
    list_display = ['get_novel_title']
    def get_novel_title(self, obj):
        return obj.novel.title
