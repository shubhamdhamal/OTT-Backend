#!/usr/bin/env python
"""
Manually sync existing encoded videos to Supabase content_media table
This fixes videos that were encoded before the content_id fix
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ott_backend.settings')
django.setup()

from hls_streaming.models import Video, HLSPlaylist
from supabase import create_client
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sync_videos():
    """Sync completed videos from Django to Supabase content_media"""
    
    print("=" * 80)
    print("[*] SYNCING EXISTING VIDEOS TO CONTENT_MEDIA")
    print("=" * 80)
    
    # Get Supabase connection
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("[X] Supabase credentials not configured!")
        return
    
    print(f"[+] Connecting to Supabase: {supabase_url}")
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all completed videos that have R2 URLs
    completed_videos = HLSPlaylist.objects.filter(
        status='completed',
        r2_uploaded=True,
        master_playlist_url__isnull=False
    ).exclude(master_playlist_url='')
    
    print(f"\n[INFO] Found {completed_videos.count()} completed videos")
    
    synced = 0
    skipped = 0
    failed = 0
    
    for hls_playlist in completed_videos:
        video_id = str(hls_playlist.video.id)
        master_url = hls_playlist.master_playlist_url
        title = hls_playlist.video.title
        
        # Generate content_id from video_id
        content_id = f'content_{video_id}'
        
        print(f"\n[VIDEO] {title} ({video_id})")
        print(f"         Master URL: {master_url}")
        print(f"         Content ID: {content_id}")
        
        try:
            # Check if already exists
            existing = supabase.table('content_media').select('id').eq(
                'content_id', content_id
            ).eq('media_type', 'video').execute()
            
            if existing.data and len(existing.data) > 0:
                print(f"         [SKIP] Already exists in content_media")
                skipped += 1
                continue
            
            # Insert media entry
            media_entry = {
                'content_id': content_id,
                'media_type': 'video',
                'file_url': master_url,
                'is_primary': True,
            }
            
            response = supabase.table('content_media').insert(media_entry).execute()
            print(f"         [OK] Created content_media entry successfully!")
            synced += 1
            
        except Exception as e:
            print(f"         [ERROR] Failed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"[RESULTS] SYNC")
    print("=" * 80)
    print(f"Synced: {synced}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Failed: {failed}")
    print("=" * 80)
    
    if synced > 0:
        print(f"\n[SUCCESS] Synced {synced} videos!")
        print("Flutter app should now be able to find these videos in content_media")
    elif failed > 0:
        print(f"\n[WARNING] Some videos failed to sync. Check errors above.")
    else:
        print(f"\n[INFO] No new videos were synced (all already exist or none qualified)")

if __name__ == '__main__':
    sync_videos()
