"""
HLS Video Management Views and Serializers
Handles video upload, encoding, and playlist serving
"""

from django.shortcuts import get_object_or_404
from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
import os
import json
import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Video, HLSPlaylist
from .serializers import VideoSerializer, HLSPlaylistSerializer
from .services import HLSStreamingService
from .r2_service import get_r2_service_from_settings
import logging
import shutil

logger = logging.getLogger(__name__)


def send_video_encoding_notification(user_email, video_title, video_id, master_playlist_url):
    """
    Send email notification when video encoding is complete
    """
    try:
        subject = f"✅ Video Encoding Complete: {video_title}"
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #2ecc71;">Video Encoding Complete!</h2>
                    
                    <p>Hello,</p>
                    
                    <p>Your video has been successfully encoded and is now ready for streaming.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Video Details:</strong><br>
                        <p style="margin: 10px 0;">
                            <strong>Title:</strong> {video_title}<br>
                            <strong>Video ID:</strong> {video_id}<br>
                            <strong>Status:</strong> Ready for Streaming
                        </p>
                    </div>
                    
                    <p>Your video is now available in your content dashboard and can be viewed by your audience.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                        <p>Best regards,<br>OTT Platform Team</p>
                        <p style="margin-top: 10px;">This is an automated notification. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        send_mail(
            subject,
            f"Video '{video_title}' has been successfully encoded and is ready for streaming.",
            settings.DEFAULT_FROM_EMAIL or 'noreply@ott-platform.com',
            [user_email],
            html_message=html_message,
            fail_silently=True
        )
        
        logger.info(f"📧 Email notification sent to {user_email} for video {video_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send email notification: {str(e)}", exc_info=True)


class VideoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing videos and HLS streaming
    Handles upload, encoding, and playlist serving
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Allow anonymous access for upload action
        Require authentication for other actions
        """
        if self.action == 'upload':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload a video file and queue it for HLS encoding (ASYNCHRONOUS - via Celery)
        POST /api/videos/upload/
        
        Expected form data:
        - video_file: The video file
        - title: Video title
        - description: Video description
        - content_id: (Optional) Content ID from admin portal
        
        ✅ RETURNS IMMEDIATELY (202 Accepted)
        Encoding happens in background via Celery worker
        Email notification sent when complete
        """
        try:
            video_file = request.FILES.get('video_file')
            if not video_file:
                return Response(
                    {"error": "No video file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file type
            allowed_extensions = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv']
            file_ext = video_file.name.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                return Response(
                    {"error": f"File type '.{file_ext}' not allowed. Allowed: {', '.join(allowed_extensions)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate unique video ID
            video_id = f"video_{uuid.uuid4().hex[:12]}"
            
            # Get content_id from request (passed from admin portal via FormData)
            # FormData is in request.POST, not request.data (which is for JSON)
            content_id = request.POST.get('content_id', None)
            if not content_id:
                content_id = request.data.get('content_id', None)  # Fallback for JSON requests
            
            # Create video object
            video = Video(
                id=video_id,
                user=request.user if request.user.is_authenticated else None,
                original_file=video_file,
                title=request.POST.get('title') or request.data.get('title', 'Untitled'),
                description=request.POST.get('description') or request.data.get('description', ''),
                status='uploading'
            )
            video.save()
            
            logger.info(f"📹 Video uploaded and saved: {video.id} - {video.title}")
            if content_id:
                logger.info(f"   Content ID: {content_id}")
            
            # Get or create HLS playlist record
            hls_playlist, created = HLSPlaylist.objects.get_or_create(video=video)
            hls_playlist.status = 'queued'
            hls_playlist.save()
            
            logger.info(f"📊 HLS Playlist created: {hls_playlist.id}, Status: queued")
            
            # ✅ QUEUE CELERY TASK (ASYNCHRONOUS - Returns immediately)
            try:
                from .tasks import encode_video_to_hls
                
                logger.info(f"🔄 Queueing encode_video_to_hls task for video: {video_id}")
                task = encode_video_to_hls.delay(video_id, content_id)
                
                logger.info(f"✅ Task queued successfully. Task ID: {task.id}")
                logger.info(f"   Video will be encoded in background")
                
                return Response(
                    {
                        "success": True,
                        "video_id": video_id,
                        "status": "queued",
                        "task_id": task.id,
                        "message": "Video queued for encoding. Check email for notification when complete."
                    },
                    status=status.HTTP_202_ACCEPTED  # 202 = Async, accepted for processing
                )
            
            except Exception as task_error:
                logger.error(f"❌ Failed to queue Celery task: {str(task_error)}", exc_info=True)
                
                # Still return success - task failed to queue but video was saved
                return Response(
                    {
                        "success": False,
                        "video_id": video_id,
                        "status": "queued_with_error",
                        "message": "Video saved but task queueing failed. Please check backend.",
                        "error": str(task_error)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            logger.error(f"❌ Upload error: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a video and its HLS files from both local storage and R2
        DELETE /api/videos/{id}/
        """
        video = self.get_object()
        video_id = str(video.id)
        
        try:
            # Get HLS playlist info
            hls_playlist = HLSPlaylist.objects.filter(video=video).first()
            
            # Delete from R2 if uploaded
            if hls_playlist and hls_playlist.r2_uploaded and hls_playlist.r2_prefix:
                try:
                    r2_service = get_r2_service_from_settings(settings)
                    if r2_service:
                        deleted_count = r2_service.delete_directory(hls_playlist.r2_prefix)
                        logger.info(f"✅ Deleted {deleted_count} files from R2: {hls_playlist.r2_prefix}")
                except Exception as e:
                    logger.error(f"⚠️  Error deleting from R2: {e}")
            
            # Delete local HLS files
            video_hls_dir = os.path.join(
                getattr(settings, 'HLS_OUTPUT_DIR', '/tmp/hls_videos'),
                video_id
            )
            if os.path.exists(video_hls_dir):
                try:
                    shutil.rmtree(video_hls_dir)
                    logger.info(f"✅ Deleted local HLS files: {video_hls_dir}")
                except Exception as e:
                    logger.error(f"⚠️  Error deleting local HLS files: {e}")
            
            # Delete original video file
            if video.original_file:
                try:
                    video.original_file.delete(save=True)
                except Exception as e:
                    logger.error(f"⚠️  Error deleting original file: {e}")
            
            # Delete database records
            logger.info(f"🗑️  Deleting video record: {video_id}")
            return super().destroy(request, *args, **kwargs)
        
        except Exception as e:
            logger.error(f"❌ Error during video deletion: {e}", exc_info=True)
            return Response(
                {"error": f"Failed to delete video: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def encoding_status(self, request, pk=None):
        """
        Get the encoding status of a video
        GET /api/videos/{id}/encoding_status/
        """
        video = self.get_object()
        
        try:
            hls_playlist = HLSPlaylist.objects.get(video=video)
            return Response({
                "video_id": video.id,
                "title": video.title,
                "status": video.status,
                "encoding_status": hls_playlist.status,
                "progress": hls_playlist.progress,
                "master_playlist_url": hls_playlist.master_playlist_url,
                "estimated_size_mb": hls_playlist.estimated_size_mb,
                "renditions": hls_playlist.get_renditions(),
                "created_at": hls_playlist.created_at,
            })
        except HLSPlaylist.DoesNotExist:
            return Response({
                "video_id": video.id,
                "title": video.title,
                "status": video.status,
                "encoding_status": "pending",
                "progress": 0,
                "message": "Encoding not started yet"
            })
    
    @action(detail=True, methods=['get'])
    def playlist(self, request, pk=None):
        """
        Get HLS master playlist
        GET /api/videos/{id}/playlist/
        """
        video = self.get_object()
        
        try:
            hls_playlist = HLSPlaylist.objects.get(video=video)
            
            if hls_playlist.status != 'completed':
                return Response(
                    {"error": f"Video encoding in progress. Status: {hls_playlist.status}"},
                    status=status.HTTP_202_ACCEPTED
                )
            
            return Response({
                "video_id": video.id,
                "title": video.title,
                "master_playlist_url": hls_playlist.master_playlist_url,
                "renditions": hls_playlist.get_renditions(),
                "codec_info": {
                    "primary": "H.265 (HEVC)",
                    "fallback": "H.264",
                    "audio": "AAC 128kbps"
                },
                "metadata": {
                    "segment_duration": 6,
                    "total_size_mb": hls_playlist.estimated_size_mb,
                }
            })
        
        except HLSPlaylist.DoesNotExist:
            return Response(
                {"error": "HLS playlist not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def download_playlist(self, request, pk=None):
        """
        Download the master HLS playlist file
        GET /api/videos/{id}/download_playlist/
        """
        video = self.get_object()
        
        try:
            hls_playlist = HLSPlaylist.objects.get(video=video)
            playlist_path = hls_playlist.get_playlist_file_path()
            
            if not os.path.exists(playlist_path):
                return Response(
                    {"error": "Playlist file not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return FileResponse(
                open(playlist_path, 'rb'),
                as_attachment=True,
                filename=f"{video.id}_master.m3u8"
            )
        
        except HLSPlaylist.DoesNotExist:
            return Response(
                {"error": "HLS playlist not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def retry_encoding(self, request, pk=None):
        """
        Retry encoding for a failed video
        POST /api/videos/{id}/retry_encoding/
        Optional body: { "content_id": "<supabase_content_id>" }
        """
        video = self.get_object()
        
        try:
            from .tasks import encode_video_to_hls

            # Accept content_id from request body so the task can update Supabase
            content_id = request.data.get('content_id') or request.POST.get('content_id')

            # Validate the original file is still present
            original_path = video.get_original_file_path()
            if not original_path or not os.path.exists(original_path):
                return Response(
                    {"error": f"Original video file no longer exists at {original_path}. Cannot retry."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Reset status so the task cycle works correctly
            video.status = 'uploading'
            video.save(update_fields=['status'])
            try:
                hls_playlist = video.hls_playlist
                hls_playlist.status = 'queued'
                hls_playlist.error_message = ''
                hls_playlist.save(update_fields=['status', 'error_message'])
            except HLSPlaylist.DoesNotExist:
                pass

            task = encode_video_to_hls.delay(video.id, content_id)
            logger.info(f"Retry task queued: video={video.id}, task={task.id}, content_id={content_id}")
            
            return Response({
                "success": True,
                "message": "Encoding task requeued",
                "video_id": video.id,
                "task_id": task.id,
            })
        
        except Exception as e:
            logger.error(f"Error retrying encoding: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@require_http_methods(["GET"])
def serve_hls_segment(request, video_id, rendition, segment_name):
    """
    Serve HLS segment files (.ts)
    GET /api/hls/{video_id}/{rendition}/{segment_name}
    """
    try:
        segment_path = os.path.join(
            settings.HLS_OUTPUT_DIR,
            video_id,
            rendition,
            segment_name
        )
        
        if not os.path.exists(segment_path):
            logger.warning(f"Segment not found: {segment_path}")
            return Response(
                {"error": "Segment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Security check - prevent directory traversal
        if not os.path.abspath(segment_path).startswith(settings.HLS_OUTPUT_DIR):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return FileResponse(
            open(segment_path, 'rb'),
            content_type='video/MP2T'
        )
    
    except Exception as e:
        logger.error(f"Error serving segment: {e}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@require_http_methods(["GET"])
def serve_hls_playlist(request, video_id, rendition):
    """
    Serve HLS playlist files (.m3u8)
    GET /api/hls/{video_id}/{rendition}/playlist.m3u8
    """
    try:
        playlist_path = os.path.join(
            settings.HLS_OUTPUT_DIR,
            video_id,
            rendition,
            "index.m3u8"
        )
        
        if not os.path.exists(playlist_path):
            logger.warning(f"Playlist not found: {playlist_path}")
            return Response(
                {"error": "Playlist not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Security check
        if not os.path.abspath(playlist_path).startswith(settings.HLS_OUTPUT_DIR):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return FileResponse(
            open(playlist_path, 'rb'),
            content_type='application/vnd.apple.mpegurl'
        )
    
    except Exception as e:
        logger.error(f"Error serving playlist: {e}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@require_http_methods(["GET"])
def serve_master_playlist(request, video_id):
    """
    Serve master HLS playlist
    GET /api/hls/{video_id}/master.m3u8
    """
    try:
        playlist_path = os.path.join(
            settings.HLS_OUTPUT_DIR,
            video_id,
            "master.m3u8"
        )
        
        if not os.path.exists(playlist_path):
            logger.warning(f"Master playlist not found: {playlist_path}")
            return Response(
                {"error": "Master playlist not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Security check
        if not os.path.abspath(playlist_path).startswith(settings.HLS_OUTPUT_DIR):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return FileResponse(
            open(playlist_path, 'rb'),
            content_type='application/vnd.apple.mpegurl'
        )
    
    except Exception as e:
        logger.error(f"Error serving master playlist: {e}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
