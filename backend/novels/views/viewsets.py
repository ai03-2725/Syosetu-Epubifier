from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import viewsets

from novels.models import EpubFile, Novel
from novels.serializers import EpubFileSerializer, NovelSerializer


class NovelViewSet(viewsets.ModelViewSet):
    
    queryset = Novel.objects.order_by('-last_fetch_timestamp').all()
    serializer_class = NovelSerializer
    
class EpubFileViewSet(viewsets.ModelViewSet):
    
    queryset = EpubFile.objects.all()
    serializer_class = EpubFileSerializer
    
    def retrieve(self, request, pk=None):
        epub = get_object_or_404(self.queryset, pk=pk)
        # serializer = NovelSerializer(novel)
        # return Response(serializer.data)
        epub_file = epub.file.open()
        return FileResponse(epub_file, as_attachment=True)
    
    
    


    
    
    

    

    

