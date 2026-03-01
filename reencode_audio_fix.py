"""
Re-encode a video whose HLS segments were encoded without stereo downmix (-ac 2).
Fixes: audio silent in Flutter app for Dolby Atmos / 5.1 / 7.1 source videos.

Usage: .\venv\Scripts\python.exe reencode_audio_fix.py
"""
import django
import os
import sys
import shutil

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ott_backend.settings')
django.setup()

from django.conf import settings
from hls_streaming.models import Video, HLSPlaylist
from hls_streaming.services import HLSStreamingService
from hls_streaming.r2_service import get_r2_service_from_settings

VIDEO_ID = 'video_07af55b9154d'
CONTENT_ID = 'content_1772345956856_oypo2s7'

v = Video.objects.get(id=VIDEO_ID)
p = v.hls_playlist

original_file = v.get_original_file_path()
print(f'Original file: {original_file}')
print(f'Original file exists: {os.path.exists(original_file)}')

if not os.path.exists(original_file):
    print('ERROR: Original file not found!')
    sys.exit(1)

hls_dir = f'/tmp/hls_videos/{VIDEO_ID}'

# Delete existing (wrongly-encoded) HLS output
if os.path.exists(hls_dir):
    shutil.rmtree(hls_dir)
    print(f'Deleted old HLS output: {hls_dir}')

# Re-encode with stereo fix (-ac 2 is now in the service)
print('Starting re-encoding with audio fix (stereo downmix)...')
p.status = 'encoding'
p.error_message = ''
p.r2_uploaded = False
p.master_playlist_url = ''
p.save()
v.status = 'uploading'
v.save(update_fields=['status'])

hls_output_dir = getattr(settings, 'HLS_OUTPUT_DIR', '/tmp/hls_videos')
service = HLSStreamingService(output_dir=hls_output_dir)

result = service.encode_to_hls(input_file=original_file, video_id=VIDEO_ID)

if not result['success']:
    print(f'Encoding FAILED: {result.get("error")}')
    p.status = 'failed'
    p.error_message = result.get('error', 'Unknown')
    p.save(update_fields=['status', 'error_message'])
    sys.exit(1)

print(f'Encoding complete. Duration: {result["duration_seconds"]:.0f}s')

# Upload to R2
print('Uploading to R2...')
r2 = get_r2_service_from_settings(settings)
if not r2:
    print('ERROR: R2 not configured!')
    sys.exit(1)

p.status = 'uploading'
p.r2_prefix = f'videos/{VIDEO_ID}'
p.save(update_fields=['status', 'r2_prefix'])

upload_result = r2.upload_directory(
    local_dir=result['output_dir'],
    r2_prefix=f'videos/{VIDEO_ID}',
    extensions=['.m3u8', '.ts']
)

files_uploaded = len(upload_result.get('success', []))
failed = upload_result.get('failed', [])
print(f'R2 upload: {files_uploaded} files uploaded, {len(failed)} failed')

if files_uploaded == 0:
    print('ERROR: Nothing was uploaded!')
    sys.exit(1)

master_url = r2.get_master_playlist_url(VIDEO_ID)
print(f'Master URL: {master_url}')

# Update Django
p.r2_uploaded = True
p.master_playlist_url = master_url
p.status = 'completed'
p.save()
v.status = 'completed'
v.save(update_fields=['status'])
print('Django DB: status=completed')

# Update Supabase
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
existing = sb.table('content_media').select('id').eq('content_id', CONTENT_ID).eq('media_type', 'video').execute()
if existing.data:
    sb.table('content_media').update({'file_url': master_url}).eq('content_id', CONTENT_ID).eq('media_type', 'video').execute()
    print('Supabase: content_media UPDATED')
else:
    sb.table('content_media').insert({'content_id': CONTENT_ID, 'media_type': 'video', 'file_url': master_url, 'is_primary': True}).execute()
    print('Supabase: content_media INSERTED')

# Cleanup temp files
shutil.rmtree(result['output_dir'], ignore_errors=True)

print()
print('SUCCESS — video re-encoded with stereo audio and re-uploaded.')
print(f'The Flutter app should now have audio.')
print(f'Master URL: {master_url}')
