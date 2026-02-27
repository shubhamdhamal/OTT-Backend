"""
Django Models for HLS Video Management
Tracks video encoding status and playlists
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import os


class Video(models.Model):
    """Model to store video metadata"""
    
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('encoding', 'Encoding'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.CharField(max_length=100, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    original_file = models.FileField(upload_to='uploads/originals/%Y/%m/%d/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    duration_seconds = models.IntegerField(null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    def get_original_file_path(self):
        """Get the absolute path to the original file"""
        return self.original_file.path if self.original_file else None


class HLSPlaylist(models.Model):
    """Model to store HLS playlist information and encoding status"""
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('pending', 'Pending'),
        ('encoding', 'Encoding'),
        ('uploading', 'Uploading to R2'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='hls_playlist')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=255, blank=True, null=True)  # Celery task ID for tracking
    progress = models.IntegerField(default=0)  # 0-100
    
    # Master playlist URLs
    master_playlist_url = models.URLField(max_length=500, blank=True)  # R2 URL
    master_playlist_local_path = models.CharField(max_length=500, blank=True)  # Temp local path
    thumbnail_url = models.URLField(max_length=500, blank=True)  # Thumbnail preview image URL
    
    # R2 Storage info
    r2_prefix = models.CharField(max_length=255, blank=True)  # e.g., "videos/video_123"
    r2_uploaded = models.BooleanField(default=False)  # Whether files are in R2
    
    # Encoding metadata
    renditions_data = models.JSONField(default=dict)  # Stores rendition info
    estimated_size_mb = models.FloatField(null=True, blank=True)
    
    # Codec info
    primary_codec = models.CharField(
        max_length=20,
        default='h265',
        choices=[('h265', 'H.265'), ('h264', 'H.264')]
    )
    fallback_codec = models.CharField(
        max_length=20,
        default='h264',
        choices=[('h265', 'H.265'), ('h264', 'H.264')]
    )
    
    # Segment configuration
    segment_duration = models.IntegerField(default=6)  # seconds
    segment_count = models.IntegerField(default=3)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Timestamps
    encoding_started_at = models.DateTimeField(null=True, blank=True)
    encoding_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['video']),
        ]
    
    def __str__(self):
        return f"HLS Playlist for {self.video.title} ({self.status})"
    
    def get_renditions(self):
        """Get list of available renditions"""
        return self.renditions_data.get('renditions', [])
    
    def set_renditions(self, renditions_dict):
        """Store renditions data"""
        self.renditions_data = {'renditions': renditions_dict}
        self.save()
    
    def get_playlist_file_path(self):
        """Get absolute path to master playlist file"""
        return self.master_playlist_local_path
    
    def mark_encoding_started(self):
        """Mark encoding as started"""
        self.status = 'encoding'
        self.encoding_started_at = timezone.now()
        self.save()
    
    def mark_encoding_completed(self, master_url, renditions, estimated_size):
        """Mark encoding as completed"""
        self.status = 'completed'
        self.encoding_completed_at = timezone.now()
        self.master_playlist_url = master_url
        self.set_renditions(renditions)
        self.estimated_size_mb = estimated_size
        self.video.status = 'completed'
        self.video.save()
        self.save()
    
    def mark_encoding_failed(self, error_message, error_traceback=''):
        """Mark encoding as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.video.status = 'failed'
        self.video.save()
        self.save()
    
    def update_progress(self, progress):
        """Update encoding progress"""
        self.progress = min(progress, 99)  # Cap at 99 until completed
        self.save()


class HLSSegment(models.Model):
    """Model to track HLS segments (optional, for segment management)"""
    
    hls_playlist = models.ForeignKey(
        HLSPlaylist,
        on_delete=models.CASCADE,
        related_name='segments'
    )
    rendition = models.CharField(max_length=50)  # e.g., "480p", "720p"
    segment_number = models.IntegerField()
    duration_seconds = models.FloatField()
    file_path = models.CharField(max_length=500)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['hls_playlist', 'rendition']),
        ]
        ordering = ['rendition', 'segment_number']
    
    def __str__(self):
        return f"{self.rendition} - Segment {self.segment_number}"
