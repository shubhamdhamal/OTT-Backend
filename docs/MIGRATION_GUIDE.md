# Migration Guide: Redis → No Redis + R2

## Quick Checklist

- [ ] Update `HLS_REQUIREMENTS.txt` (remove Celery/Redis, add boto3)
- [ ] Create `r2_service.py`
- [ ] Update `models.py` (add R2 fields)
- [ ] Update `views.py` (sync encoding)
- [ ] Update `HLS_DJANGO_SETTINGS_CONFIG.py` (R2 config)
- [ ] Update `docker-compose.yml` (remove Redis/Celery)
- [ ] Update `.env` (R2 credentials)
- [ ] Remove `tasks.py` usage from codebase
- [ ] Run migrations
- [ ] Test upload

## Step-by-Step

### 1. Update Dependencies

```bash
# Remove old requirements
pip uninstall celery redis -y

# Install new
pip install -r HLS_REQUIREMENTS.txt
# Should now include: boto3
```

### 2. Copy New Files

```bash
# Copy r2_service.py to hls_streaming directory
cp r2_service.py hls_streaming/
```

### 3. Database Migration

```bash
python manage.py makemigrations hls_streaming
python manage.py migrate
```

### 4. Update Django Settings

**Remove:**
```python
# DELETE THESE:
CELERY_BROKER_URL = 'redis://...'
CELERY_RESULT_BACKEND = 'redis://...'
CELERY_TASK_SERIALIZER = 'json'
# ... all Celery settings
```

**Add:**
```python
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', 'ott-videos')

HLS_OUTPUT_DIR = '/tmp/hls_videos'  # Temp directory
```

### 5. Set Environment Variables

```bash
cat > .env << EOF
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=ott-videos
EOF
```

### 6. Update Docker Compose (Optional)

```bash
# If using Docker, update docker-compose.yml
# Remove Redis service
# Remove Celery service
# Add R2 env vars to web service
```

### 7. Verify R2 Connection

```bash
python manage.py shell
>>> from hls_streaming.r2_service import get_r2_service_from_settings
>>> from django.conf import settings
>>> r2 = get_r2_service_from_settings(settings)
>>> if r2:
...     print("✅ R2 connected")
... else:
...     print("❌ R2 not configured")
```

### 8. Test Upload

**Using API:**
```bash
curl -X POST http://localhost:8000/api/v1/videos/upload/ \
  -H "Authorization: Token your-token" \
  -F "video_file=@small_test_video.mp4" \
  -F "title=Test Video"
```

**Monitor logs:**
```bash
tail -f /var/log/hls_streaming.log
```

**Watch for:**
```
🎬 Starting HLS encoding...
✅ Encoding completed
📤 Uploading to R2...
✅ Uploaded: https://...
🗑️  Deleting local files
```

## What Happens to Old Code?

### Old Structure (with Celery)

```python
# views.py
def upload(self, request):
    # ... save video ...
    encode_video_to_hls.delay(video.id)  # Queue task
    return Response({"status": "queued"})

# tasks.py
@shared_task
def encode_video_to_hls(video_id):
    # ... encode ...
    # Save to disk
    # Return URL
```

### New Structure (sync + R2)

```python
# views.py
def upload(self, request):
    # ... save video ...
    
    # SYNCHRONOUS encoding
    service = HLSStreamingService()
    result = service.encode_to_hls(input_file)
    
    # Upload to R2
    r2.upload_directory(result['output_dir'])
    
    # Delete local files
    shutil.rmtree(result['output_dir'])
    
    return Response({"status": "completed", "url": r2_url})
```

## Rollback Plan

If you need to go back to Redis + Celery:

```bash
# Revert changes
git checkout HLS_REQUIREMENTS.txt
git checkout hls_streaming/views.py
git checkout hls_streaming/models.py
git checkout docker-compose.yml

# Reinstall old deps
pip install celery redis

# Restore from git history
git log --oneline | grep "celery"
git checkout <commit-hash> -- .
```

## Performance Comparison

| Metric | With Celery | Without Celery |
|--------|-----------|----------------|
| Upload endpoint response time | 2s (returns immediately) | 15-30min (blocks) |
| Server complexity | High (Redis + workers) | Low (just Django) |
| Failed encodings | Easier to retry | Must re-upload |
| Scaling | Add workers | Upgrade CPU |
| Video discovery lag | Minutes | Immediate |

## Cost Analysis

### With Redis + Local Storage
```
- Redis instance: $20-50/month
- Server storage: $50-200/month (500GB+)
- Worker nodes: $50-100/month (2+ per region)
- Total: ~$120-350/month
```

### With R2 Storage Only
```
- R2 storage: $0.02/GB
- R2 bandwidth: $0.02/GB
- Server: Same as before
- Total: ~$30-50/month (for 1TB)
```

## Troubleshooting Migration

### Error: "R2 not configured"

```python
# Check settings
python -c "from django.conf import settings; print(settings.R2_ACCOUNT_ID)"

# Should print: your-account-id (not None)
```

### Error: "Import error: r2_service"

```bash
# Make sure file exists
ls -la hls_streaming/r2_service.py

# Make sure permissions are correct
chmod 644 hls_streaming/r2_service.py
```

### Error: "Upload hangs indefinitely"

```bash
# Check HTTP timeout at load balancer
# nginx: proxy_read_timeout should be 1800s+
# Gunicorn: --timeout 1800

# Monitor encoding progress
tail -f /var/log/hls_streaming.log

# Check FFmpeg is running
ps aux | grep ffmpeg
```

### Error: "Files not appearing in R2"

```bash
# Test R2 connection
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... \
aws s3 ls s3://ott-videos/ \
  --endpoint-url https://YOUR_ACCOUNT.r2.cloudflarestorage.com \
  --recursive
```

## FAQ

**Q: Do I lose video history?**
A: No, database records are preserved. Only encoding method changes.

**Q: Can I keep both systems running?**
A: Yes, during transition:
- Old uploads use Celery + local storage
- New uploads use sync + R2
- Migration doesn't interfere

**Q: What about videos already encoded?**
A: They stay on disk or wherever they were. Point URLs to R2 or CDN as needed.

**Q: Do I need to re-encode all videos?**
A: No, only new uploads use the new system. Old videos keep working.

**Q: How do I migrate old videos to R2?**
A: Create a batch script:

```python
# migrate_to_r2.py
from hls_streaming.models import HLSPlaylist
from hls_streaming.r2_service import get_r2_service_from_settings
from django.conf import settings
import os
import shutil

r2 = get_r2_service_from_settings(settings)

for playlist in HLSPlaylist.objects.filter(r2_uploaded=False):
    video_id = playlist.video.id
    local_dir = f"/var/media/hls_videos/{video_id}"
    
    if os.path.exists(local_dir):
        # Upload to R2
        r2.upload_directory(local_dir, f"videos/{video_id}")
        
        # Update DB
        playlist.r2_uploaded = True
        playlist.master_playlist_url = r2.get_master_playlist_url(video_id)
        playlist.save()
        
        print(f"✅ Migrated {video_id}")
```

## Next Steps

1. ✅ Back up database
2. ✅ Set up R2 bucket + credentials
3. ✅ Follow migration steps above
4. ✅ Test with small video first
5. ✅ Monitor logs carefully
6. ✅ Gradually migrate production

## Support

If you get stuck:
1. Check logs: `tail -f /var/log/hls_streaming.log`
2. Verify R2 credentials
3. Test small videos first
4. Contact support with logs
