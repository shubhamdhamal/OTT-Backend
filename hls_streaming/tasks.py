"""
Celery Tasks for HLS Video Encoding
Handles async video encoding to HLS format with timeout protection
"""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
import logging
import os
import json
import shutil
from pathlib import Path
import traceback

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


@shared_task(bind=True, time_limit=60*60, soft_time_limit=55*60, max_retries=2)
def encode_video_to_hls(self, video_id, content_id=None):
    """
    Async task to encode video to HLS format and upload to R2
    
    TIME LIMITS:
    - Soft limit: 55 minutes (graceful shutdown signal - allow cleanup)
    - Hard limit: 60 minutes (1 hour force kill to prevent hanging processes)
    
    Args:
        video_id: ID of the video to encode
        content_id: (Optional) ID of the content from admin portal
        
    Returns:
        dict: Task result with success status and URLs
    """
    try:
        # Import here to avoid circular imports
        from .models import Video, HLSPlaylist
        from .services import HLSStreamingService
        from .r2_service import get_r2_service_from_settings
        from django.db import connection, connections
        
        logger.info(f"🎬 [Celery Task {self.request.id}] Starting HLS encoding for video: {video_id}")
        
        # Get video object
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            logger.error(f"❌ Video not found: {video_id}")
            return {"success": False, "error": "Video not found"}
        
        # Get or create HLS playlist record
        hls_playlist, created = HLSPlaylist.objects.get_or_create(video=video)
        hls_playlist.status = 'encoding'
        hls_playlist.task_id = self.request.id
        hls_playlist.save(update_fields=['status', 'task_id'])
        
        logger.info(f"📊 Status: hls_playlist.status = 'encoding', task_id = {self.request.id}")
        
        # Get input file path
        input_file = video.get_original_file_path()
        if not input_file or not os.path.exists(input_file):
            error_msg = f"Input file not found: {input_file}"
            logger.error(f"❌ {error_msg}")
            hls_playlist.status = 'failed'
            hls_playlist.error_message = error_msg
            hls_playlist.save(update_fields=['status', 'error_message'])
            video.status = 'failed'
            video.save(update_fields=['status'])
            return {"success": False, "error": error_msg}
        
        logger.info(f"📄 Input file: {input_file} ({os.path.getsize(input_file) / (1024**3):.2f}GB)")
        
        # ⚠️ CLOSE DB CONNECTION BEFORE LONG-RUNNING ENCODING
        # FFmpeg encoding can take 20+ minutes, so we close the connection now
        # and get a fresh one after encoding completes
        connections.close_all()
        logger.info(f"🔌 Closed database connections before long encoding operation")
        
        try:
            # STEP 1: Encode to HLS
            logger.info(f"🔄 [Step 1/4] Starting HLS encoding process...")
            hls_output_dir = getattr(settings, 'HLS_OUTPUT_DIR', '/tmp/hls_videos')
            service = HLSStreamingService(output_dir=hls_output_dir)
            
            encoding_result = service.encode_to_hls(
                input_file=input_file,
                video_id=video_id
            )
            
            if not encoding_result['success']:
                error_msg = encoding_result.get('error', 'Unknown encoding error')
                logger.error(f"❌ Encoding failed: {error_msg}")
                hls_playlist.status = 'failed'
                hls_playlist.error_message = error_msg
                hls_playlist.save(update_fields=['status', 'error_message'])
                video.status = 'failed'
                video.save(update_fields=['status'])
                return {"success": False, "error": error_msg}
            
            logger.info(f"✅ [Step 1/4] HLS encoding completed successfully")
            
            # ⚠️ REOPEN DB CONNECTION AFTER LONG ENCODING
            # The FFmpeg encoding took 20+ minutes, so we need a fresh DB connection
            from django.db import connections
            connections.close_all()
            
            # Force a fresh connection by accessing the db
            _ = Video.objects.filter(id=video_id).first()
            logger.info(f"🔌 Reopened database connection after encoding")
            
            # STEP 2: Update video duration
            try:
                duration_seconds = int(encoding_result.get('duration_seconds', 0))
                video.duration_seconds = duration_seconds
                video.save(update_fields=['duration_seconds'])
                logger.info(f"⏱️  [Step 2/4] Video duration updated: {duration_seconds // 60}m {duration_seconds % 60}s")
            except Exception as e:
                logger.warning(f"⚠️  Could not update duration: {str(e)}")
            
            # STEP 3: R2 Upload
            logger.info(f"📤 [Step 3/4] Starting R2 upload...")
            hls_playlist.status = 'uploading'
            hls_playlist.save(update_fields=['status'])
            
            r2_service = get_r2_service_from_settings(settings)
            if not r2_service:
                error_msg = "R2 service not configured"
                logger.error(f"❌ {error_msg}")
                hls_playlist.status = 'failed'
                hls_playlist.error_message = error_msg
                hls_playlist.save(update_fields=['status', 'error_message'])
                video.status = 'failed'
                video.save(update_fields=['status'])
                return {"success": False, "error": error_msg}
            
            video_output_dir = encoding_result['output_dir']
            r2_prefix = f"videos/{video_id}"
            
            logger.info(f"R2 Prefix: {r2_prefix}")
            
            upload_results = r2_service.upload_directory(
                local_dir=video_output_dir,
                r2_prefix=r2_prefix,
                extensions=['.m3u8', '.ts']
            )
            
            if not upload_results['success']:
                error_msg = "Failed to upload to R2"
                logger.error(f"❌ {error_msg}")
                hls_playlist.status = 'failed'
                hls_playlist.error_message = error_msg
                hls_playlist.save(update_fields=['status', 'error_message'])
                video.status = 'failed'
                video.save(update_fields=['status'])
                return {"success": False, "error": error_msg}
            
            logger.info(f"✅ [Step 3/4] R2 upload completed: {upload_results.get('files_uploaded', 0)} files")
            
            # STEP 4: Update playlist and finalize
            logger.info(f"🎯 [Step 4/4] Finalizing and storing R2 URLs...")
            
            hls_playlist.r2_prefix = r2_prefix
            hls_playlist.r2_uploaded = True
            master_playlist_url = r2_service.get_master_playlist_url(video_id)
            hls_playlist.master_playlist_url = master_playlist_url
            
            renditions = []
            for rendition_name, rendition_data in encoding_result['renditions'].items():
                renditions.append({
                    "name": rendition_name,
                    "hevc": rendition_data.get('hevc', False),
                    "h264": rendition_data.get('h264', False),
                    "url": f"{master_playlist_url.replace('master.m3u8', '')}{rendition_name}/index.m3u8"
                })
            
            hls_playlist.set_renditions(renditions)
            hls_playlist.estimated_size_mb = encoding_result.get('estimated_total_size_mb', 0)
            hls_playlist.status = 'completed'
            hls_playlist.save()
            
            video.status = 'completed'
            video.save(update_fields=['status'])
            
            logger.info(f"✅ [Step 4/4] Finalization completed")
            logger.info(f"📊 Master Playlist: {master_playlist_url}")
            logger.info(f"🎬 Renditions: {', '.join([r['name'] for r in renditions])}")
            
            # 🔗 STEP 5: Create media entry in Supabase for the app to fetch
            try:
                logger.info(f"📝 [Step 5/5] Creating media entry in Supabase...")
                logger.info(f"   content_id parameter: {content_id}")
                
                from supabase import create_client
                
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                
                if not supabase_url or not supabase_key:
                    logger.error(f"❌ Supabase credentials missing!")
                    logger.error(f"   SUPABASE_URL: {supabase_url}")
                    logger.error(f"   SUPABASE_SERVICE_ROLE_KEY: {'***' if supabase_key else 'NOT SET'}")
                    raise Exception("Supabase credentials not configured")
                
                logger.info(f"🔗 Connecting to Supabase: {supabase_url}")
                supabase = create_client(supabase_url, supabase_key)
                logger.info(f"✅ Supabase client created successfully")
                
                # Use content_id from admin portal, or generate one
                if not content_id:
                    logger.warning(f"⚠️  No content_id provided by admin portal, using fallback")
                    effective_content_id = f'content_{video_id}'
                else:
                    logger.info(f"✅ Using content_id from admin: {content_id}")
                    effective_content_id = content_id
                
                # Create media entry for master playlist
                media_entry = {
                    'content_id': effective_content_id,
                    'media_type': 'video',
                    'file_url': master_playlist_url,
                    'is_primary': True,
                }
                
                logger.info(f"📤 Inserting to content_media table:")
                logger.info(f"   {media_entry}")
                
                response = supabase.table('content_media').insert(media_entry).execute()
                
                logger.info(f"✅ Media entry created successfully!")
                logger.info(f"   Content ID: {effective_content_id}")
                logger.info(f"   Media Type: video")
                logger.info(f"   Master URL: {master_playlist_url}")
                logger.info(f"   Reachable at: https://example.com/contents/{effective_content_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create media entry in Supabase: {str(e)}", exc_info=True)
                logger.error(f"   This means Flutter app will NOT be able to find the video!")
            
        except Exception as e:
            error_msg = f"Encoding exception: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            hls_playlist.status = 'failed'
            hls_playlist.error_message = error_msg
            hls_playlist.save(update_fields=['status', 'error_message'])
            video.status = 'failed'
            video.save(update_fields=['status'])
            return {"success": False, "error": error_msg}
        
        # Clean up temporary files
        try:
            video_output_dir = encoding_result.get('output_dir')
            if video_output_dir and os.path.exists(video_output_dir):
                shutil.rmtree(video_output_dir)
                logger.info(f"🗑️  Cleaned up temporary files: {video_output_dir}")
        except Exception as e:
            logger.warning(f"⚠️  Could not clean up temp files: {str(e)}")
        
        # Send email notification
        try:
            if video.user and video.user.email:
                send_video_encoding_notification(
                    video.user.email,
                    video.title,
                    video_id,
                    hls_playlist.master_playlist_url
                )
        except Exception as e:
            logger.warning(f"⚠️  Could not send email notification: {str(e)}")
        
        logger.info(f"✅ [Celery Task {self.request.id}] ENCODING SUCCESSFULLY COMPLETED for {video_id}")
        return {
            'success': True,
            'video_id': video_id,
            'master_playlist_url': hls_playlist.master_playlist_url,
            'status': 'completed'
        }
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in encode_video_to_hls: {str(e)}", exc_info=True)
        try:
            from .models import Video, HLSPlaylist
            video = Video.objects.get(id=video_id)
            hls_playlist = HLSPlaylist.objects.get(video=video)
            hls_playlist.status = 'failed'
            hls_playlist.error_message = f"Unexpected error: {str(e)}"
            hls_playlist.save(update_fields=['status', 'error_message'])
            video.status = 'failed'
            video.save(update_fields=['status'])
        except:
            pass
        
        return {
            'success': False,
            'video_id': video_id,
            'error': str(e),
            'status': 'failed'
        }
    try:
        # Import here to avoid circular imports
        from .models import Video, HLSPlaylist
        from .services import HLSStreamingService
        
        logger.info(f"🎬 Starting HLS encoding task for video: {video_id}")
        
        # Get video object
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            logger.error(f"❌ Video not found: {video_id}")
            return {"success": False, "error": "Video not found"}
        
        # Get or create HLS playlist record
        hls_playlist, created = HLSPlaylist.objects.get_or_create(video=video)
        hls_playlist.mark_encoding_started()
        
        # Get input file path
        input_file = video.get_original_file_path()
        if not input_file or not os.path.exists(input_file):
            error_msg = f"Input file not found: {input_file}"
            logger.error(f"❌ {error_msg}")
            hls_playlist.mark_encoding_failed(error_msg)
            return {"success": False, "error": error_msg}
        
        logger.info(f"📁 Input file: {input_file}")
        
        # Initialize HLS service
        hls_output_dir = getattr(settings, 'HLS_OUTPUT_DIR', '/tmp/hls_videos')
        service = HLSStreamingService(output_dir=hls_output_dir)
        
        try:
            # Start encoding
            logger.info(f"🎬 Starting encoding...")
            encoding_result = service.encode_to_hls(
                input_file=input_file,
                video_id=video_id
            )
            
            if not encoding_result['success']:
                error_msg = encoding_result.get('error', 'Unknown encoding error')
                logger.error(f"❌ Encoding failed: {error_msg}")
                hls_playlist.mark_encoding_failed(error_msg)
                return {"success": False, "error": error_msg}
            
            logger.info(f"✅ Encoding completed successfully")
            
            # Update video metadata
            video.duration_seconds = int(encoding_result.get('duration_seconds', 0))
            video.save()
            
            # Construct CDN URLs
            cdn_base_url = getattr(settings, 'HLS_CDN_BASE_URL', '')
            if cdn_base_url:
                master_url = f"{cdn_base_url}/{video_id}/master.m3u8"
            else:
                # Local serving fallback
                master_url = f"/api/hls/{video_id}/master.m3u8"
            
            # Prepare renditions data
            renditions = []
            for rendition_name, rendition_data in encoding_result['renditions'].items():
                renditions.append({
                    "name": rendition_name,
                    "hevc": rendition_data.get('hevc', False),
                    "h264": rendition_data.get('h264', False),
                    "url": f"/api/hls/{video_id}/{rendition_name}/playlist.m3u8"
                })
            
            # Update HLS playlist record
            hls_playlist.mark_encoding_completed(
                master_url=master_url,
                renditions=renditions,
                estimated_size=encoding_result.get('estimated_total_size_mb', 0)
            )
            
            logger.info(
                f"✅ HLS encoding completed for {video_id}. "
                f"Size: {encoding_result.get('estimated_total_size_mb', 0):.2f}MB"
            )
            
            # Log rendition details
            logger.info(f"📊 Renditions created:")
            for rendition_name, rendition_data in encoding_result['renditions'].items():
                codecs_str = ""
                if rendition_data.get('hevc'):
                    codecs_str += "H.265 "
                if rendition_data.get('h264'):
                    codecs_str += "H.264 "
                logger.info(f"   {rendition_name}: {codecs_str.strip()}")
            
            return {
                "success": True,
                "video_id": video_id,
                "master_url": master_url,
                "size_mb": encoding_result.get('estimated_total_size_mb', 0),
                "renditions": renditions
            }
        
        except Exception as e:
            logger.error(f"❌ Exception during encoding: {str(e)}", exc_info=True)
            hls_playlist.mark_encoding_failed(
                error_message=str(e),
                error_traceback=traceback.format_exc()
            )
            
            # Retry task with exponential backoff
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    
    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


@shared_task
def cleanup_old_encodings(days=30):
    """
    Cleanup old HLS encoding files
    
    Args:
        days: Delete encodings older than X days
    """
    try:
        from .models import HLSPlaylist
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        old_playlists = HLSPlaylist.objects.filter(
            encoding_completed_at__lt=cutoff_date,
            delete_after_days__isnull=False
        )
        
        count = 0
        for playlist in old_playlists:
            try:
                hls_output_dir = getattr(settings, 'HLS_OUTPUT_DIR', '/tmp/hls_videos')
                video_dir = os.path.join(hls_output_dir, playlist.video.id)
                
                if os.path.exists(video_dir):
                    import shutil
                    shutil.rmtree(video_dir)
                    logger.info(f"🗑️  Cleaned up: {video_dir}")
                    count += 1
            except Exception as e:
                logger.warning(f"Could not cleanup {playlist.video.id}: {e}")
        
        logger.info(f"✅ Cleanup completed. Directories removed: {count}")
        return {"success": True, "cleaned_count": count}
    
    except Exception as e:
        logger.error(f"❌ Cleanup task failed: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def generate_hls_thumbnail(video_id, timestamp_seconds=5):
    """
    Generate thumbnail from video for HLS preview
    
    Args:
        video_id: ID of the video
        timestamp_seconds: Timestamp to capture thumbnail from
    """
    try:
        import subprocess
        from .models import Video
        
        video = Video.objects.get(id=video_id)
        input_file = video.get_original_file_path()
        
        if not input_file or not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return {"success": False, "error": "Input file not found"}
        
        # Output thumbnail path
        hls_output_dir = getattr(settings, 'HLS_OUTPUT_DIR', '/tmp/hls_videos')
        thumb_path = os.path.join(hls_output_dir, video_id, 'thumbnail.jpg')
        Path(thumb_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Extract thumbnail using FFmpeg
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-ss', str(timestamp_seconds),
            '-vframes', '1',
            '-vf', 'scale=320:180',
            thumb_path,
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info(f"✅ Thumbnail generated: {thumb_path}")
            return {"success": True, "thumbnail_path": thumb_path}
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return {"success": False, "error": result.stderr}
    
    except Exception as e:
        logger.error(f"❌ Thumbnail generation failed: {e}")
        return {"success": False, "error": str(e)}
