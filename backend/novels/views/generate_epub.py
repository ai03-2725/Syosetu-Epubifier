
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from novels.utils.enqueue_generate_epub_with_metadata import enqueue_generate_epub_task

@api_view(['POST'])
def generate_epub_for_novel(request: Request):
    """
    Starts an epub generation task for the given novel ID
    """
    if request.method != "POST":
        return Response(status=400)
    
    novel_id = request.data.get("novelId")
    if novel_id is None:
        return Response({"error": "novelIdを指定してください"}, status=400)
    
    # Enqueue epub generation task
    return_value = enqueue_generate_epub_task(novel_id)
    return Response({"error": return_value["error"], "jobId": return_value["job_id"]}, status=200 if return_value["error"] is None else 400)