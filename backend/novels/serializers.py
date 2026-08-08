from rest_framework import serializers

from novels.models import Chapter, Episode, EpubFile, Novel, UploadedImage

class NovelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Novel
        fields = "__all__"
        
class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = "__all__"
        
class EpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Episode
        fields = "__all__"

class EpisodeSerializerWithoutContents(serializers.ModelSerializer):
    class Meta:
        model = Episode
        fields = [
            "id",
            "chapter",
            "episode_number", 
            "episode_title", 
            "last_known_update_timestamp"
            ]
        
class UploadedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = "__all__"
        
class EpubFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EpubFile
        fields = "__all__"
        
