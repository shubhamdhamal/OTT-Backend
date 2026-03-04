#!/usr/bin/env python
"""
Fix: manually set the video URL in content_media for a specific content.

Usage (run on VPS from /path/to/OTT-Backend):
    python fix_video_url.py <content_id> <master_playlist_url>

Example:
    python fix_video_url.py content_1772660787188_iejx0e2 \
        https://pub-93e8482a2a254b0d86fd3e49d6e0833d.r2.dev/videos/video_e888be3e4ed0/master.m3u8

Also prints a diagnostic of ALL content_media rows for that content_id so you
can see exactly what Celery wrote.
"""

import os, sys
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Args ───────────────────────────────────────────────────────────────────────
if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)

content_id = sys.argv[1]
video_url  = sys.argv[2]

print(f"\n{'='*70}")
print(f"Content ID : {content_id}")
print(f"Video URL  : {video_url}")
print(f"{'='*70}\n")

# ── Diagnostic: show all current content_media rows for this content ───────────
rows = supabase.table('content_media').select('*').eq('content_id', content_id).execute()
print(f"[DIAG] content_media rows for {content_id}:")
if rows.data:
    for r in rows.data:
        print(f"  - media_type={r.get('media_type')}, file_url={r.get('file_url')!r}, is_primary={r.get('is_primary')}")
else:
    print("  (none found)")

# Also check if Celery used the fallback ID
import os, sys
# Derive potential fallback IDs from the video URL
# URL pattern: videos/<video_id>/master.m3u8
import re
m = re.search(r'videos/(video_[^/]+)/master\.m3u8', video_url)
if m:
    django_video_id = m.group(1)
    fallback_id = f'content_{django_video_id}'
    fallback_rows = supabase.table('content_media').select('*').eq('content_id', fallback_id).execute()
    if fallback_rows.data:
        print(f"\n[DIAG] Found rows under FALLBACK id '{fallback_id}':")
        for r in fallback_rows.data:
            print(f"  - media_type={r.get('media_type')}, file_url={r.get('file_url')!r}, is_primary={r.get('is_primary')}")
    else:
        print(f"\n[DIAG] No rows under fallback id '{fallback_id}'")

# ── Fix: upsert the video URL ──────────────────────────────────────────────────
print(f"\n[FIX] Upserting video URL into content_media ...")

video_row = next((r for r in rows.data if r.get('media_type') == 'video'), None)

if video_row:
    result = supabase.table('content_media').update({
        'file_url': video_url,
        'is_primary': True,
    }).eq('id', video_row['id']).execute()
    print(f"[OK]  Updated existing video row (id={video_row['id']})")
else:
    result = supabase.table('content_media').insert({
        'content_id': content_id,
        'media_type': 'video',
        'file_url': video_url,
        'is_primary': True,
    }).execute()
    print(f"[OK]  Inserted new video row")

# ── Verify ─────────────────────────────────────────────────────────────────────
verify = supabase.table('content_media').select('*') \
    .eq('content_id', content_id).eq('media_type', 'video').execute()
final_url = verify.data[0]['file_url'] if verify.data else 'NOT FOUND'
print(f"\n[VERIFY] file_url is now: {final_url}")
print("\nDone. Reload the app to see the video.\n")
