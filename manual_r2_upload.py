"""
One-shot script to upload already-encoded HLS files to R2 and update Supabase.
Run with: .\venv\Scripts\python.exe manual_r2_upload.py
"""
import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ott_backend.settings')
django.setup()

from django.conf import settings
from hls_streaming.models import Video, HLSPlaylist
from hls_streaming.r2_service import get_r2_service_from_settings

VIDEO_ID = 'video_07af55b9154d'
CONTENT_ID = 'content_1772345956856_oypo2s7'

v = Video.objects.get(id=VIDEO_ID)
p = v.hls_playlist

hls_dir = f'/tmp/hls_videos/{VIDEO_ID}'
master_path = f'{hls_dir}/master.m3u8'

print(f'HLS output dir: {hls_dir}')
print(f'master.m3u8 exists: {os.path.exists(master_path)}')

if not os.path.exists(master_path):
    print('ERROR: master.m3u8 not found! Run encoding first.')
    sys.exit(1)

# Count files to upload
ts_files = sum(1 for r, d, files in os.walk(hls_dir) for f in files)
print(f'Files to upload to R2: {ts_files}')

print('Connecting to R2...')
r2 = get_r2_service_from_settings(settings)
if not r2:
    print('ERROR: R2 service not configured! Check R2_* env vars.')
    sys.exit(1)

print('R2 connected. Starting upload (may take a few minutes for a large video)...')
try:
    result = r2.upload_directory(
        local_dir=hls_dir,
        r2_prefix=f'videos/{VIDEO_ID}',
        extensions=['.m3u8', '.ts']
    )
except Exception as upload_exc:
    import traceback
    print(f'EXCEPTION during upload_directory:')
    traceback.print_exc()
    sys.exit(1)

files_uploaded = len(result.get('success', []))
failed = result.get('failed', [])
print(f'Upload result: files_uploaded={files_uploaded} failed={len(failed)}')
print(f'Full result keys: {list(result.keys())}')

if failed:
    print(f'First failed file: {failed[0]}')

if not files_uploaded and failed:
    print('Upload completely failed!')
    sys.exit(1)

if files_uploaded == 0:
    print('ERROR: No files were uploaded!')
    print('Result:', result)
    sys.exit(1)

master_url = r2.get_master_playlist_url(VIDEO_ID)
print(f'Master playlist URL: {master_url}')

# Update Django DB
p.r2_prefix = f'videos/{VIDEO_ID}'
p.r2_uploaded = True
p.master_playlist_url = master_url
p.status = 'completed'
p.save()
v.status = 'completed'
v.save(update_fields=['status'])
print('Django DB updated: status=completed')

# Update Supabase content_media
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

media_entry = {
    'content_id': CONTENT_ID,
    'media_type': 'video',
    'file_url': master_url,
    'is_primary': True,
}
existing = sb.table('content_media').select('id').eq('content_id', CONTENT_ID).eq('media_type', 'video').execute()
if existing.data:
    sb.table('content_media').update({'file_url': master_url, 'is_primary': True}).eq('content_id', CONTENT_ID).eq('media_type', 'video').execute()
    print(f'Supabase content_media UPDATED for content_id={CONTENT_ID}')
else:
    sb.table('content_media').insert(media_entry).execute()
    print(f'Supabase content_media INSERTED for content_id={CONTENT_ID}')

# Update encoding_ref if it exists
sb.table('content_media').update({
    'file_url': f'completed:{VIDEO_ID}',
    'file_name': f'django_video_id:{VIDEO_ID}:completed',
}).eq('content_id', CONTENT_ID).eq('media_type', 'encoding_ref').execute()

print()
print('SUCCESS! Video is now LIVE.')
print(f'  Content ID: {CONTENT_ID}')
print(f'  Master URL: {master_url}')
print('The mobile app should now show the video instead of "retry".')
