#!/usr/bin/env python
"""
Re-encode existing videos to fix truncated HLS playlists.
Videos encoded with SEGMENT_COUNT=3 only have ~18 seconds in playlist.
This re-queues them with the fixed SEGMENT_COUNT=0 (full VOD).
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ott_backend.settings')
django.setup()

from hls_streaming.models import Video, HLSPlaylist
from hls_streaming.tasks import encode_video_to_hls
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("=" * 60)
print("RE-ENCODE VIDEOS WITH FIXED HLS CONFIG (VOD full playlist)")
print("=" * 60)

# Get all videos that have the original file on disk (regardless of status)
videos = Video.objects.all()
queued = 0
skipped = 0

for video in videos:
    original_file = video.original_file.path if video.original_file else None

    if not original_file or not os.path.exists(original_file):
        print(f"[SKIP] {video.id} ({video.title}) - original file not on disk")
        skipped += 1
        continue

    # Get content_id from Supabase
    resp = supabase.table('content_media').select('content_id').eq(
        'media_type', 'video'
    ).like('file_url', f'%{video.id}%').execute()

    content_id = resp.data[0]['content_id'] if resp.data else None

    print(f"[QUEUE] {video.id} ({video.title})")
    print(f"        File: {original_file}")
    print(f"        Content ID: {content_id}")

    # Reset status so task processes it
    video.status = 'uploading'
    video.save(update_fields=['status'])

    hls = HLSPlaylist.objects.filter(video=video).first()
    if hls:
        hls.status = 'queued'
        hls.save(update_fields=['status'])

    # Queue re-encode
    task = encode_video_to_hls.delay(video.id, content_id)
    print(f"        Task ID: {task.id}")
    queued += 1

print()
print("=" * 60)
print(f"Queued: {queued}")
print(f"Skipped (no file): {skipped}")
print("=" * 60)
if queued:
    print("Celery worker will re-encode and update Supabase URLs.")
