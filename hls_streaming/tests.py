"""
Tests for HLS Streaming App
"""

from django.test import TestCase
from django.contrib.auth.models import User
from .models import Video, HLSPlaylist, HLSSegment


class VideoModelTest(TestCase):
    """Tests for Video model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_video_creation(self):
        """Test creating a video object"""
        video = Video(
            id='test_video_1',
            user=self.user,
            title='Test Video',
            description='A test video',
            status='uploading'
        )
        video.save()
        
        self.assertEqual(video.title, 'Test Video')
        self.assertEqual(video.status, 'uploading')
        self.assertEqual(video.user, self.user)


class HLSPlaylistModelTest(TestCase):
    """Tests for HLSPlaylist model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.video = Video.objects.create(
            id='test_video_1',
            user=self.user,
            title='Test Video',
            status='uploading'
        )
    
    def test_hls_playlist_creation(self):
        """Test creating an HLS playlist"""
        playlist = HLSPlaylist.objects.create(
            video=self.video,
            status='pending',
            primary_codec='h265'
        )
        
        self.assertEqual(playlist.video, self.video)
        self.assertEqual(playlist.status, 'pending')
        self.assertEqual(playlist.primary_codec, 'h265')
    
    def test_renditions_storage(self):
        """Test storing rendition data"""
        playlist = HLSPlaylist.objects.create(video=self.video)
        
        renditions = {
            '480p': {'hevc': True, 'h264': True},
            '720p': {'hevc': True, 'h264': False}
        }
        
        playlist.set_renditions(renditions)
        retrieved_renditions = playlist.get_renditions()
        
        self.assertEqual(retrieved_renditions, renditions)
