"""
URL Configuration for HLS Streaming App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, serve_hls_segment, serve_hls_playlist, serve_master_playlist

router = DefaultRouter()
router.register(r'videos', VideoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('hls/<str:video_id>/master.m3u8', serve_master_playlist, name='master-playlist'),
    path('hls/<str:video_id>/<str:rendition>/playlist.m3u8', serve_hls_playlist, name='hls-playlist'),
    path('hls/<str:video_id>/<str:rendition>/<str:segment_name>', serve_hls_segment, name='hls-segment'),
]
