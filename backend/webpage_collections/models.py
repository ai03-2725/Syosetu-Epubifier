from django.db import models

# Create your models here.
from enum import Enum
from typing import Literal

from django.db import models

class CollectionStatusChoices(Enum):
    ACTIVE = "連載中"
    COMPLETED = "完結"


class WebpageCollection(models.Model):
    # The novel itself
    title = models.TextField(db_comment="Collection title")
    authors = models.JSONField(db_comment="JSON-stored list of authors", default=list) 
    status = models.TextField(db_comment="Novel status (i.e. actively being written, completed, etc.)", choices=[(choice.name, choice.value) for choice in CollectionStatusChoices])
    last_updated_timestamp = models.DateTimeField(db_comment="The last known timestamp at which this novel was modified")
    last_fetch_timestamp = models.DateTimeField(db_comment="The last timestamp at which this novel was fetched/rescanned")
    frozen = models.BooleanField(default=False, db_comment="Whether fetching for this novel has been disabled or not")
    
class WebpageStatusChoices(Enum):
    ACTIVE = "連載中"
    COMPLETED = "完結"
    
    
class Webpage(models.Model):
    title = models.TextField(db_comment="Webpage title")
    authors = models.JSONField(db_comment="JSON-stored list of authors", default=list) 
    source = models.TextField(db_comment="Webpage source URL")
    last_updated_timestamp = models.DateTimeField(db_comment="The last known timestamp at which this novel was modified")
    last_fetch_timestamp = models.DateTimeField(db_comment="The last timestamp at which this novel was fetched/rescanned")