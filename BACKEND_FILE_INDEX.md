# OTT Backend File Structure

## Backend Django App: hls_streaming/

Complete Django application for HLS video streaming with adaptive bitrate encoding.

### Core Python Files

#### `services.py` (~450 lines)
**FFmpeg-based HLS encoding service**
- `HLSEncodingConfig`: Configuration for encoding (480p, 720p, H.265/H.264)
- `HLSStreamingService`: Main service for video encoding
  - `_check_ffmpeg()`: Verify FFmpeg installation
  - `_get_video_duration()`: Extract video duration
  - `_encode_rendition_hevc()`: Encode with H.265 codec
  - `_encode_rendition_h264()`: Encode with H.264 fallback
  - `_create_master_playlist()`: Create HLS master playlist
  - `encode_to_hls()`: Main encoding method

#### `models.py` (~150 lines)
**Django ORM models for video management**
- `Video`: Store video metadata (title, description, status)
- `HLSPlaylist`: HLS encoding status and metadata
  - Methods: `mark_encoding_started()`, `mark_encoding_completed()`, `mark_encoding_failed()`
- `HLSSegment`: Track individual HLS segments

#### `views.py` (~280 lines)
**REST API endpoints for video upload and streaming**
- `VideoViewSet`: Main ViewSet with actions:
  - `upload()`: Accept video files
  - `encoding_status()`: Get encoding progress
  - `playlist()`: Get master playlist URL
  - `download_playlist()`: Download playlist file
  - `retry_encoding()`: Retry failed encoding
- Standalone views:
  - `serve_hls_segment()`: Serve .ts segment files
  - `serve_hls_playlist()`: Serve .m3u8 playlist files
  - `serve_master_playlist()`: Serve master.m3u8

#### `tasks.py` (~200 lines)
**Celery async tasks for background encoding**
- `encode_video_to_hls()`: Main encoding task
  - Async video encoding to HLS format
  - FFmpeg integration
  - Error handling with retries
  - Progress tracking
- `cleanup_old_encodings()`: Delete old encoded videos
- `generate_hls_thumbnail()`: Extract video thumbnail

#### `serializers.py` (~120 lines)
**Django REST Framework serializers**
- `VideoSerializer`: Serialize video data
- `HLSPlaylistSerializer`: Serialize HLS playlist info
- `HLSSegmentSerializer`: Serialize segment info
- `VideoUploadSerializer`: Validate video upload
- `EncodingStatusSerializer`: Format status response

#### `urls.py` (~20 lines)
**URL routing for HLS API**
- `/api/v1/videos/` → VideoViewSet
- `/api/v1/videos/{id}/upload/` → Upload endpoint
- `/api/v1/videos/{id}/encoding_status/` → Status endpoint
- `/api/v1/hls/{video_id}/master.m3u8` → Master playlist
- `/api/v1/hls/{video_id}/{rendition}/playlist.m3u8` → Rendition playlist
- `/api/v1/hls/{video_id}/{rendition}/*.ts` → Segments

#### `admin.py` (~30 lines)
**Django admin interface**
- Video admin interface
- HLSPlaylist admin interface
- HLSSegment admin interface

#### `apps.py` (~10 lines)
**Django app configuration**

#### `tests.py` (~100 lines)
**Unit tests**
- VideoModelTest: Video model tests
- HLSPlaylistModelTest: HLS playlist tests

#### `__init__.py`
**Package initialization**

### Django App Structure

```
hls_streaming/
├── migrations/
│   └── __init__.py
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── serializers.py
├── services.py
├── tasks.py
├── tests.py
├── urls.py
└── views.py
```

## Backend Configuration Files

### `HLS_DJANGO_SETTINGS_CONFIG.py` (~100 lines)
**Django settings template**
- HLS_OUTPUT_DIR configuration
- INSTALLED_APPS setup
- Celery configuration
- REST Framework settings
- CORS configuration
- Logging setup

### `.env.example`
**Environment variables template**
- Django settings
- Database credentials
- HLS paths
- Redis connection
- Email configuration
- CORS settings

### `HLS_REQUIREMENTS.txt`
**Python dependencies**
- Django 4.2.0
- djangorestframework 3.14.0
- django-cors-headers 4.0.0
- celery 5.2.7
- redis 4.5.1
- Pillow (image processing)
- python-dotenv (env variables)

## Deployment Files

### `docker-compose.yml`
**Complete Docker setup**
- PostgreSQL database
- Redis cache/queue
- Django web application
- Celery worker
- Persistent volumes

### `Dockerfile`
**Container image**
- Based on Python 3.10
- FFmpeg installation
- PostgreSQL client
- Python dependencies
- Auto-migration on start

### `hls_setup.sh`
**Automated setup script**
- Create virtual environment
- Install dependencies
- Create directories
- Run migrations
- Start services

### `urls_config.py`
**Django URL configuration**
- Admin routes
- API v1 routes
- Media file serving

## Documentation Files

### `README_HLS_BACKEND.md` (~200 lines)
**Main backend documentation**
- Quick start guide
- Installation steps
- API endpoint reference
- Configuration guide
- Docker deployment
- Production checklist

### `hls_validate.py` (~250 lines)
**System validation tool**
- Check Python version
- Verify FFmpeg installation
- Test Redis connectivity
- Validate Django setup
- Check directory permissions
- Generate validation report

## File Statistics

| File | Lines | Purpose |
|------|-------|---------|
| services.py | ~450 | FFmpeg encoding service |
| models.py | ~150 | ORM models |
| views.py | ~280 | REST API endpoints |
| tasks.py | ~200 | Celery async tasks |
| serializers.py | ~120 | DRF serializers |
| admin.py | ~30 | Django admin |
| apps.py | ~10 | App config |
| urls.py | ~20 | URL routing |
| tests.py | ~100 | Unit tests |
| **Total App Code** | **~1,360** | **Core application** |
| HLS_DJANGO_SETTINGS_CONFIG.py | ~100 | Settings template |
| docker-compose.yml | ~80 | Docker orchestration |
| Dockerfile | ~30 | Container image |
| hls_validate.py | ~250 | Validation tool |
| hls_setup.sh | ~40 | Setup script |
| **Total Backend** | **~1,860** | **Complete system** |

## Deployment Flow

1. **Development**
   - Use `docker-compose up` for full stack
   - Or manual `python manage.py runserver`

2. **Testing**
   - Run `python hls_validate.py`
   - Execute `python manage.py test`

3. **Production**
   - Deploy with Docker or systemd
   - Use gunicorn + nginx
   - Configure PostgreSQL + Redis
   - Set appropriate environment variables

## Key Features

✅ **Video Upload**: Multipart form upload support
✅ **Async Encoding**: Celery-based background tasks
✅ **Dual Codec**: H.265 primary + H.264 fallback
✅ **Adaptive Bitrate**: 480p (800k) + 720p (1400k)
✅ **REST API**: Full video management endpoints
✅ **HLS Streaming**: Master and variant playlists
✅ **Error Handling**: Retry logic with exponential backoff
✅ **Monitoring**: Validation tools and logging
✅ **Docker Ready**: Production-ready containers
✅ **Admin Interface**: Django admin for management

## Integration

To integrate with Django project:

1. Add to INSTALLED_APPS:
   ```python
   'hls_streaming',
   ```

2. Include URLs in main urls.py:
   ```python
   path('api/v1/', include('hls_streaming.urls')),
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Configure settings (see HLS_DJANGO_SETTINGS_CONFIG.py)

5. Start Celery worker for encoding tasks
