"""
Django REST Framework Serializers for HLS Video Management
"""

from rest_framework import serializers
from .models import Video, HLSPlaylist, HLSSegment


class HLSPlaylistSerializer(serializers.ModelSerializer):
    """Serializer for HLS Playlist"""
    
    class Meta:
        model = HLSPlaylist
        fields = [
            'video',
            'status',
            'progress',
            'master_playlist_url',
            'renditions_data',
            'estimated_size_mb',
            'primary_codec',
            'fallback_codec',
            'segment_duration',
            'segment_count',
            'encoding_started_at',
            'encoding_completed_at',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'encoding_started_at',
            'encoding_completed_at',
        ]


class VideoSerializer(serializers.ModelSerializer):
    """Serializer for Video"""
    
    hls_playlist = HLSPlaylistSerializer(read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'description',
            'original_file',
            'status',
            'duration_seconds',
            'file_size_bytes',
            'hls_playlist',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'duration_seconds',
            'file_size_bytes',
            'created_at',
            'updated_at',
        ]


class HLSSegmentSerializer(serializers.ModelSerializer):
    """Serializer for HLS Segment"""
    
    class Meta:
        model = HLSSegment
        fields = [
            'hls_playlist',
            'rendition',
            'segment_number',
            'duration_seconds',
            'file_path',
            'file_size_bytes',
            'created_at',
        ]
        read_only_fields = [
            'created_at',
        ]


class VideoUploadSerializer(serializers.Serializer):
    """Serializer for video upload"""
    
    video_file = serializers.FileField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    
    def validate_video_file(self, value):
        """Validate video file"""
        allowed_extensions = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv']
        file_ext = value.name.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '.{file_ext}' not allowed. "
                f"Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (e.g., max 1GB)
        max_size = 1024 * 1024 * 1024  # 1GB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size ({value.size / 1024 / 1024:.0f}MB) exceeds maximum "
                f"({max_size / 1024 / 1024:.0f}MB)"
            )
        
        return value


class EncodingStatusSerializer(serializers.Serializer):
    """Serializer for encoding status response"""
    
    video_id = serializers.CharField()
    title = serializers.CharField()
    status = serializers.CharField()
    encoding_status = serializers.CharField()
    progress = serializers.IntegerField()
    master_playlist_url = serializers.CharField(required=False)
    estimated_size_mb = serializers.FloatField(required=False)
    renditions = serializers.ListField(required=False)
    error_message = serializers.CharField(required=False)
