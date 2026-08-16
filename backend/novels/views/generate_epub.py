
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
    
    novel_ids = request.data.get("novelIds")
    # Handle cases where novelIds simply isn't defined
    if novel_ids is None:
        return Response({"error": "novelIdsを指定してください"}, status=400)
    # Handle case where novelIds is True = autofetch all - proceed as-is
    elif isinstance(novel_ids, bool) and novel_ids is True:
        pass
    # Otherwise novelIds should be a list of IDs
    # Handle cases where it isn't
    elif not isinstance(novel_ids, list) or not all(isinstance(novel_id, int) for novel_id in novel_ids):
        return Response({"error": "novelIdsはIDのリストかTrueとして指定ください"}, status=400)
    # Otherwise should be fine
    
    # Enqueue epub generation task
    return_value = enqueue_generate_epub_task(novel_ids)
    return Response({"error": return_value["error"], "jobIds": return_value["job_ids"]}, status=200 if return_value["error"] is None else 400)