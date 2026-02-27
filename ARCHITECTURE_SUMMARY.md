# Architecture Summary: No Redis + R2 Storage

## What You Asked For

✅ **No Redis mode** - Works without Redis
✅ **Encode → Upload → Delete** - Local encode, upload to R2, clean up
✅ **Adaptive bitrate on app** - HLS native, player auto-selects quality

## The New Architecture

```
┌─────────────────┐
│  Client Upload  │
│  (small video)  │
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│   Django Upload      │
│   Endpoint           │
│   (POST /upload)     │
└────────┬─────────────┘
         │
         ▼ Synchronous
┌──────────────────────┐
│  FFmpeg Encode       │ ⏱️ 5-30 minutes
│  /tmp/hls_videos/    │ (blocks request)
│  ├── 480p/           │
│  ├── 720p/           │
│  └── master.m3u8     │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Upload to R2        │
│  (boto3)             │
│  All files → R2      │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Store R2 URLs       │
│  in Database         │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Delete Local Files  │
│  /tmp cleaned up     │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Return Response to Client               │
│  {                                       │
│    "status": "completed",                │
│    "master_url": "https://r2.../..."     │
│  }                                       │
└──────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  App Player (Flutter + Chewie)          │
│  ├─ Reads master.m3u8                   │
│  ├─ Detects 480p + 720p renditions      │
│  ├─ Measures bandwidth                  │
│  ├─ Auto-switches quality               │
│  └─ User sees smooth playback           │
└─────────────────────────────────────────┘
```

## Key Differences

### Before: Async + Local Storage
```
Upload → Queue → Background Worker → Disk → CDN URL
└─ Response: "queued"
```

### Now: Sync + R2
```
Upload → Encode (blocks) → Upload R2 → DB → Response
└─ Response: "completed" with R2 URL
```

## Files Changed

| File | Change | Why |
|------|--------|-----|
| `r2_service.py` | NEW | Upload to R2 |
| `views.py` | Sync encoding | Remove Celery |
| `models.py` | Add r2_uploaded | Track R2 status |
| `services.py` | Return paths | For R2 upload |
| `tasks.py` | (unused) | No longer needed |
| `docker-compose.yml` | Remove Redis/Celery | Simpler setup |
| `HLS_REQUIREMENTS.txt` | Add boto3 | For R2 SDK |
| `HLS_DJANGO_SETTINGS_CONFIG.py` | Add R2 config | R2 credentials |
| `.env.example` | Add R2 vars | Configuration |

## What Stays the Same

✅ FFmpeg encoding (480p + 720p)
✅ HLS streaming format
✅ PostgreSQL database
✅ Django REST API
✅ Admin portal
✅ Flutter app (just use Chewie)

## What's Different

| Aspect | Before | Now |
|--------|--------|-----|
| Queue | Redis (needed) | Not needed |
| Workers | Celery (needed) | Not needed |
| Encode Time | Async (fast response) | Sync (blocks request) |
| Storage | Server disk | R2 bucket |
| Cleanup | Manual | Automatic |
| Scaling | Add workers | Upgrade CPU |
| Complexity | High | Low |
| Cost | $120-350/mo | $30-50/mo |

## Pros & Cons

### Pros ✅
- **No Redis** - Can't break, don't need to monitor
- **No Celery workers** - Fewer things to deploy
- **Cheaper** - R2 is incredibly cheap
- **Simpler** - Single deployment unit
- **Immediate** - URLs ready instantly
- **Reliable** - No queue failures

### Cons ⚠️
- **Blocks upload** - 30 min for large videos
- **Needs HTTP timeout** - Configure load balancer
- **Server CPU** - FFmpeg is CPU intensive
- **Vertical scaling** - Can't just add workers

## Quick Start

### 1. Install
```bash
pip install -r HLS_REQUIREMENTS.txt
```

### 2. Configure
```bash
# .env
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=ott-videos
```

### 3. Migrate
```bash
python manage.py migrate
```

### 4. Test
```bash
curl -X POST http://localhost/api/v1/videos/upload/ \
  -F "video_file=@video.mp4" \
  -F "title=Test"

# Wait 5-30 minutes... encoding in progress!
```

### 5. Monitor
```bash
tail -f /var/log/hls_streaming.log
```

## Adaptive Bitrate Streaming Implementation

### Backend (Done)
✅ Encodes 480p @ 800kbps
✅ Encodes 720p @ 1400kbps
✅ Creates master.m3u8 with both

### Frontend (Easy)
```dart
// Flutter app
Chewie(
  controller: ChewieController(
    videoPlayerController: VideoPlayerController.network(
      'https://r2-url/master.m3u8'
    ),
    autoPlay: true,
  ),
)

// That's it! ABR works automatically:
// - Player measures bandwidth
// - Player selects 480p or 720p
// - Player switches during playback
```

**No special code needed. HLS player handles it.**

## Network Speed Adaptation

```
Fast WiFi (>2 Mbps)    → 720p @ 1400k (HD)
    ↓
Mobile 4G (1-2 Mbps)   → 720p or 480p (auto)
    ↓
Mobile 3G (0.5-1 Mbps) → 480p @ 800k (SD)
    ↓
Slow/Congested         → 480p (lower quality)

Player measures in real-time and switches!
```

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│  Load Balancer                          │
│  - Timeout: 1800s (30 minutes)          │
│  - Path: /api/v1/videos/upload/         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Django Server (1+)                     │
│  - FFmpeg installed                     │
│  - 2+ CPU cores                         │
│  - 2GB+ RAM                             │
│  - /tmp has 50GB free                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  PostgreSQL                             │
│  - Video metadata                       │
│  - R2 URLs                              │
│  - Encoding status                      │
└─────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Cloudflare R2                          │
│  - Store HLS segments                   │
│  - Store playlists                      │
│  - Global CDN                           │
│  - Public read access                   │
└─────────────────────────────────────────┘
```

## Comparison Table

| Feature | Redis/Celery | No Redis/R2 |
|---------|-------------|------------|
| Setup complexity | High | Low |
| Docker images | 3+ (web, redis, celery) | 1 (web) |
| Dependencies | celery, redis, RabbitMQ | boto3 |
| Encoding concurrency | High (many workers) | Lower (single process) |
| Response time | Instant ("queued") | 15-30 min |
| Storage | Server/attached disk | R2 (cheap) |
| Bandwidth cost | High (self-hosted) | Low (R2) |
| Failure recovery | Complex | Simple (re-upload) |
| Monitoring | Many moving parts | Just FFmpeg logs |
| Scaling | Add workers | Upgrade CPU |
| Cost (1TB/mo) | $150-300 | $30-50 |

## Monitoring

### Key Metrics
```bash
# CPU usage
top -p $(pgrep ffmpeg)

# Disk space
df -h /tmp

# Encoding progress
tail -f /var/log/hls_streaming.log

# R2 uploads
aws s3 ls s3://ott-videos/ --endpoint-url ... --recursive
```

### Health Check
```bash
# Test R2 connectivity
python manage.py shell
>>> from hls_streaming.r2_service import get_r2_service_from_settings
>>> r2 = get_r2_service_from_settings(settings)
>>> if r2: print("✅ R2 OK")
```

## Support Docs

📖 [NO_REDIS_R2_SETUP.md](NO_REDIS_R2_SETUP.md) - Detailed setup guide
📖 [ADAPTIVE_BITRATE_GUIDE.md](ADAPTIVE_BITRATE_GUIDE.md) - ABR implementation
📖 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migrate from old system

## Summary

✅ **Works without Redis**
✅ **Simpler infrastructure**
✅ **Much cheaper (R2)**
✅ **Adaptive bitrate built-in**
✅ **Easy to deploy**

⚠️ **Upload blocks for 15-30 minutes**
⚠️ **Needs HTTP timeout configured**
⚠️ **Vertical scaling only**

**Perfect for:**
- Smaller platforms (1000s of videos)
- Learning/prototypes
- Cost-conscious deployments
- Simpler operations

**Not ideal for:**
- Very high upload volume
- Immediate video availability needed
- Limited server resources
