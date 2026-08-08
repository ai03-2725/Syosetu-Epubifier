from django.urls import include, path

from novels.views.fetch_novel import get_all_fetch_novel_tasks, start_fetch_novel_task
from novels.views.generate_epub import generate_epub_for_novel
from novels.views.get_job_status import get_job_status
from novels.views.update_novel import get_all_update_novel_tasks, start_update_novels_task
from .views import viewsets
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'novels', viewsets.NovelViewSet, basename='novel')
router.register(r'epub-files', viewsets.EpubFileViewSet, basename='epubfile')

urlpatterns = [
    path('', include(router.urls)),
    path('new-novel/', start_fetch_novel_task),
    path('update-novels/', start_update_novels_task),
    path('job-status/', get_job_status),
    path('all-fetch-tasks/', get_all_fetch_novel_tasks),
    path('all-update-tasks/', get_all_update_novel_tasks),
    path('generate-epub/', generate_epub_for_novel),
]