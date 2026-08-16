from enum import Enum
from typing import Literal

from django.db import models

# class NovelStatusChoices(Enum):
#     ACTIVE = "連載中"
#     COMPLETED = "完結"
#     ABANDONED = "未完"


class Novel(models.Model):
    # The novel itself
    title = models.TextField(db_comment="Novel title")
    author = models.TextField(db_comment="Author name")
    source = models.TextField(db_comment="Source URL", unique=True)
    # status = models.TextField(db_comment="Novel status (i.e. actively being written, completed, etc.)", choices=[(choice.name, choice.value) for choice in NovelStatusChoices])
    tags = models.JSONField(default=list, db_comment="List of ovel tags as strings (if any; empty list if none or not supported)")
    last_updated_timestamp = models.DateTimeField(db_comment="The last known timestamp at which this novel was modified by the author")
    last_fetch_timestamp = models.DateTimeField(db_comment="The last timestamp at which this novel was fetched/rescanned")
    frozen = models.BooleanField(default=False, db_comment="Whether fetching for this novel has been disabled or not")
    # Post-processing flags
    postprocess_reduce_blank_lines = models.BooleanField(default=True, db_comment="Whether or not to reduce the amount of blank newlines")
    postprocess_indent_separators = models.BooleanField(default=True, db_comment="Whether or not to indent lines which appear to be separators (lines comprised of just symbols)")
    postprocess_replace_hrs = models.BooleanField(default=True, db_comment="Whether or not to replace <hr/> tags with less intrusive alternatives")
    postprocess_auto_indent = models.BooleanField(default=True, db_comment="Whether or not to indent all lines which start with text (and aren't already indented)")
    
class Chapter(models.Model):
    # Groups of episodes
    # Structure:
    # - Group 0: The landing page overview text + any chapters before the first named chapter (i.e. on sites such as syosetu.org)
    # - Group 1 onwards: Each named chapter
    # These simply slot in as title pages/sections in the resulting epub
    # pk = models.CompositePrimaryKey("novel_id", "chapter_number")
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE)
    chapter_number = models.BigIntegerField(db_comment="Chapter number") # Start with 1 for human readability if it ever gets referenced within the epub output
    chapter_title = models.TextField(blank=True, db_comment="Chapter title") # If blank (i.e. does not exist for group 0), use the book title instead
    
class Episode(models.Model):
    # Each episode (i.e. each group of novel text)
    # pk = models.CompositePrimaryKey("chapter_id", "episode_number")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    episode_number = models.BigIntegerField(db_comment="Episode number")
    episode_title = models.TextField(db_comment="Episode title")
    last_known_update_timestamp = models.DateTimeField(db_comment="The last known timestamp at which this episode was updated (used for tracking revisions)", null=True) # If null, update checks are performed by comparing contents
    contents = models.TextField(db_comment="The HTML content for the episode contents")
    
class UploadedImage(models.Model):
    # Local copies of uploaded images embedded within novels
    source_src = models.TextField(db_comment="The original image path", unique=True)
    image_file = models.ImageField(upload_to="embedded_images")
    
class EpubFile(models.Model):
    novel = models.OneToOneField(Novel, on_delete=models.CASCADE, primary_key=True)
    file = models.FileField(upload_to="epub_out")
    