from django.conf import settings
from django_rest_typescript_generator.build import build

from novels.serializers import ChapterSerializer, EpisodeSerializer, EpisodeSerializerWithoutContents, EpubFileSerializer, NovelSerializer, UploadedImageSerializer

BUILD_DIR = settings.BASE_DIR.parent / "frontend" / "src" / "types"

BUILD_TASKS = [
    build(NovelSerializer, {"alias": "Novel"}),
    build(ChapterSerializer, {"alias": "Chapter"}),
    build(EpisodeSerializer, {"alias": "Episode"}),
    build(EpisodeSerializerWithoutContents, {"alias": "EpisodeWithoutContents"}),
    build(UploadedImageSerializer, {"alias": "UploadedImage"}),
    build(EpubFileSerializer, {"alias": "EpubFile"}),
]