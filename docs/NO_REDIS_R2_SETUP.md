# No Redis + R2 Storage Setup Guide

## Overview

This guide explains the **synchronous encoding** + **R2 storage** architecture:
- ✅ No Redis required
- ✅ No Celery workers needed
- ✅ Encode locally → Upload to R2 → Delete local files
- ✅ Adaptive bitrate streaming (HLS native)
- ✅ Significantly cheaper infrastructure

## What Changed

### Before (Async + Local Storage)
```
Client Upload → Django → Queue to Celery (Redis) → Background Worker Encodes
                                                  → Files stored on server disk
                                                  → Return CDN URL
```

### Now (Sync + R2)
```
Client Upload → Django → Encode locally/temp → Upload to R2 → Store R2 URL → Delete local
```

## Prerequisites

1. **Python 3.8+**
2. **FFmpeg with libx265** (same as before)
3. **PostgreSQL** (same as before)
4. **Cloudflare R2 Account** (NEW)
5. **boto3** dependency (NEW)

## Installation

### 1. Install Dependencies

```bash
cd OTT-Backend
pip install -r HLS_REQUIREMENTS.txt
```

### 2. Create Cloudflare R2 Bucket

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **Storage → R2**
3. Click **Create Bucket**
4. Name it: `ott-videos`
5. Allow public read access for playback

### 3. Create R2 API Token

1. In R2 dashboard, click **Settings**
2. Scroll to **API Tokens**
3. Click **Create API token**
4. Name: `OTT Backend`
5. Permissions: **Object Read/Write**
6. Save credentials:
   - Bucket name
   - Account ID
   - Access Key ID
   - Secret Access Key

### 4. Configure Environment

Update `.env` with:

```env
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=ott-videos
```

### 5. Update Django Settings

Add to your Django `settings.py`:

```python
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# HLS Configuration
HLS_OUTPUT_DIR = '/tmp/hls_videos'

# R2 Configuration
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', 'ott-videos')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'ott_backend'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Remove any CELERY settings!
```

### 6. Run Migrations

```bash
python manage.py makemigrations hls_streaming
python manage.py migrate
```

### 7. Start Server

```bash
# Single terminal - no background workers needed!
python manage.py runserver
```

## How It Works

### Upload Flow

```
1. Client POSTs video file
2. Django saves to temp location
3. FFmpeg encodes → /tmp/hls_videos/video_id/{480p,720p,master.m3u8}
4. R2Service.upload_directory() uploads all files to R2
5. Database stores R2 URLs
6. Local files deleted
7. Response returned with R2 master.m3u8 URL
```

### Timing

For a typical video:
- Small (1-2 hrs, 500MB): **5-10 minutes**
- Large (3+ hrs, 1.5GB): **20-30 minutes**

⚠️ **Configure HTTP timeouts appropriately!**

### R2 Cost Estimate

```
1000 videos × 750 MB average = 750 GB
50 streams/day × 0.5 GB = 25 GB downloaded/day

Monthly Cost:
- Storage: 750 GB × $0.02 = $15
- Bandwidth: 750 GB × $0.02 = $15
- Total: ~$30/month

Much cheaper than server storage + CDN!
```

## Adaptive Bitrate Streaming (ABR)

HLS is **inherently adaptive**. No special backend code needed!

### How It Works

1. **Master Playlist** (`master.m3u8`)
   ```m3u8
   #EXTM3U
   #EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=854x480,CODECS="hev1.1.6.L120"
   480p/index.m3u8
   
   #EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=1280x720,CODECS="hev1.1.6.L120"
   720p/index.m3u8
   ```

2. **Client Play** (`master.m3u8`)
   - HLS player reads master playlist
   - Detects available bitrates
   - Measures network speed
   - **Automatically selects quality**
   - Switches during playback based on bandwidth

### Frontend Implementation (Flutter)

Use a proper HLS player:

**Option 1: HLS Package**
```dart
dependency:
  video_player: ^2.7.0
  chewie: ^1.7.0  # HLS-aware wrapper

// Automatically handles ABR!
VideoPlayerController.network(
  'https://r2-url.com/videos/123/master.m3u8'
);
```

**Option 2: Native Android/iOS**
- Android: ExoPlayer supports HLS + ABR natively
- iOS: AVPlayer supports HLS + ABR natively

### Backend Serves Optimal Master Playlist

Your current implementation already does this:

```python
def _create_master_playlist(self, output_dir: str, use_h265: bool = True) -> bool:
    # Creates playlist with multiple renditions
    # Player automatically selects based on network
```

## Monitoring & Debugging

### Check R2 Uploads

```bash
# List files in R2 bucket
aws s3 ls s3://ott-videos/videos/ --endpoint-url https://your-account.r2.cloudflarestorage.com --recursive
```

### Monitor Encoding

```bash
# Watch logs
tail -f /var/log/hls_streaming.log

# Check temp files
ls -lh /tmp/hls_videos/
```

### Test R2 Connection

```bash
python manage.py shell

from hls_streaming.r2_service import get_r2_service_from_settings
from django.conf import settings

r2 = get_r2_service_from_settings(settings)
if r2:
    print("✅ R2 connected!")
else:
    print("❌ R2 not configured")
```

## Deployment Checklist

### Load Balancer Settings

```nginx
# Set request timeout to 30+ minutes
proxy_read_timeout 1800s;
proxy_connect_timeout 1800s;
proxy_send_timeout 1800s;
```

### Server Requirements

```
- Disk: At least 50GB free in /tmp
- CPU: 2+ cores for FFmpeg
- RAM: 2GB+ for encoding buffer
- Network: Good upload speed to R2
```

### Environment Setup

```bash
# .env file
DEBUG=False
SECRET_KEY=gen-random-secret
DB_PASSWORD=strong-password
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
```

### Docker Deployment

```bash
# No Redis needed!
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## Troubleshooting

### Video Upload Hangs

**Problem:** Upload page hangs during encoding

**Solutions:**
1. Check  Nginx/load balancer timeout is 30+ minutes
2. Monitor CPU: `top` - should be high during encoding
3. Check disk space: `df -h /tmp`
4. FFmpeg logs in `/var/log/hls_streaming.log`

### R2 Upload Fails

**Problem:** Files not appearing in R2

**Solutions:**
1. Verify credentials: `python manage.py shell`
2. Check bucket name matches
3. Ensure public read access on bucket
4. Check AWS CLI: `aws s3 ls ... --endpoint-url ...`

### Adaptive Bitrate Not Working

**Problem:** Player stuck on 720p even on slow connection

**Solutions:**
1. Verify master.m3u8 has both 480p + 720p
2. Check logs for encoding errors
3. Use HLS.js or ExoPlayer (naive players don't support ABR)
4. Set player bandwidth estimate: `player.bandwidth = 2000000`

## Comparison: Before vs After

| Feature | With Redis | Without Redis |
|---------|-----------|--------------|
| Components | Redis + Celery | Just Python |
| Storage | Server disk | R2 bucket |
| Encoding | Async (background) | Sync (blocks upload) |
| Scaling | Horizontal (workers) | Vertical (faster CPU) |
| Complexity | High | Low |
| Cost | Redis + disk space | Just R2 storage |
| Latency | High (queue delay) | Low (no queue) |
| Timeout Issues | No | Need 30+ min timeout |

## API Examples

### Upload Video

```bash
curl -X POST http://localhost:8000/api/v1/videos/upload/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "video_file=@video.mp4" \
  -F "title=My Video" \
  -F "description=A great video"

# Response
{
  "success": true,
  "message": "Video uploaded and encoded successfully",
  "video_id": "video_123",
  "status": "completed",
  "master_playlist_url": "https://account.r2.cloudflarestorage.com/bucket/videos/video_123/master.m3u8"
}
```

### Check Status

```bash
curl -X GET http://localhost:8000/api/v1/videos/video_123/encoding_status/ \
  -H "Authorization: Token YOUR_TOKEN"

# Response
{
  "video_id": "video_123",
  "title": "My Video",
  "status": "completed",
  "encoding_status": "completed",
  "master_playlist_url": "https://...",
  "renditions": [
    {
      "name": "480p",
      "hevc": true,
      "h264": true,
      "url": "https://.../480p/index.m3u8"
    },
    {
      "name": "720p",
      "hevc": true,
      "h264": true,
      "url": "https://.../720p/index.m3u8"
    }
  ]
}
```

## Next Steps

1. ✅ Install dependencies
2. ✅ Set up R2 bucket + API token
3. ✅ Configure `.env`
4. ✅ Update Django settings
5. ✅ Run migrations
6. ✅ Test upload via admin or API
7. ✅ Monitor `/var/log/hls_streaming.log`
8. ✅ Configure load balancer timeouts for production
9. ✅ Test with mobile app playback

## Support

For issues:
1. Check logs: `tail -f /var/log/hls_streaming.log`
2. Verify R2 credentials with test script
3. Monitor disk space during encoding
4. Ensure FFmpeg is installed: `ffmpeg -version`
