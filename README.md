# OTT Backend

Django REST API backend for the OTT streaming platform. Handles video ingestion, HLS encoding, Cloudflare R2 storage, and Supabase database sync.

## Stack

| Layer | Technology |
|---|---|
| API Framework | Django 4.2 + Django REST Framework |
| Async Tasks | Celery 5.6 + Redis 7 |
| Video Encoding | FFmpeg (H.265 / H.264 adaptive HLS) |
| Object Storage | Cloudflare R2 (HLS segments + manifests) |
| Database | Supabase PostgreSQL |
| WSGI Server | Gunicorn |
| Containerisation | Docker + Docker Compose |

---

## Quick Start (local development)

```bash
# 1. Clone and enter the backend directory
cd OTT-Backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and fill in all required values

# 5. Apply migrations
python manage.py migrate

# 6. Start Django dev server
python manage.py runserver

# 7. In a separate terminal — start Celery worker
celery -A ott_backend worker --loglevel=info --pool=solo   # Windows
# celery -A ott_backend worker --loglevel=info             # Linux
```

Redis must be running locally (or set `CELERY_BROKER_URL` in `.env` to a remote Redis).

---

## Production Deployment (Docker)

```bash
# Build and start all services (web + celery + redis)
docker compose up -d --build

# Run migrations
docker compose exec web python manage.py migrate

# Create admin superuser
docker compose exec web python manage.py createsuperuser

# View logs
docker compose logs -f web
docker compose logs -f celery
```

For full VPS setup (Nginx, SSL, firewall) see [`vps_deploy.sh`](vps_deploy.sh).

---

## Environment Variables

Copy `.env.example` → `.env` and fill in:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `False` in production |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `DB_HOST` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Supabase PostgreSQL credentials |
| `SUPABASE_URL` / `SUPABASE_KEY` | Supabase project URL and service-role key |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Cloudflare R2 credentials |
| `R2_BUCKET_NAME` / `R2_PUBLIC_DOMAIN` | R2 bucket name and CDN domain |
| `CELERY_BROKER_URL` | Redis URL (default: `redis://redis:6379/0`) |

---

## Project Structure

```
OTT-Backend/
├── hls_streaming/          # Main Django app
│   ├── models.py           # Video, HLSPlaylist models
│   ├── views.py            # API ViewSets (upload, retry, status)
│   ├── tasks.py            # Celery task: encode_video_to_hls
│   ├── services.py         # FFmpeg encoding service (H.265 + H.264)
│   ├── r2_service.py       # Cloudflare R2 upload/delete helpers
│   ├── serializers.py      # DRF serializers
│   └── urls.py             # App URL patterns
├── ott_backend/
│   ├── settings.py         # Django settings
│   ├── celery.py           # Celery app config
│   ├── urls.py             # Root URL conf
│   └── wsgi.py
├── media/uploads/          # Original uploaded video files
├── Dockerfile              # Multi-stage production Docker image
├── docker-compose.yml      # web + celery + redis services
├── gunicorn_config.py      # Gunicorn worker config
├── requirements.txt        # Pinned Python dependencies
├── .env.example            # Environment variable template
├── vps_deploy.sh           # MilesWeb VPS setup automation
└── docs/                   # Extended documentation
    ├── ARCHITECTURE_SUMMARY.md
    ├── ADAPTIVE_BITRATE_GUIDE.md
    ├── DJANGO_PROJECT_SETUP.md
    ├── SUPABASE_SETUP.md
    ├── MIGRATION_GUIDE.md
    └── ...
```

---

## HLS Encoding Pipeline

```
POST /api/v1/videos/upload/
        │
        ▼
  Video saved to media/uploads/originals/
        │
        ▼
  Celery task queued → encode_video_to_hls
        │
        ▼
  FFmpeg encodes to /tmp/hls_videos/<video_id>/
  ├── 1080p  (H.265 + H.264 fallback)
  ├── 720p
  ├── 480p
  └── master.m3u8
        │
        ▼
  Files uploaded to Cloudflare R2
  └── <bucket>/hls/<video_id>/
        │
        ▼
  Supabase content_media record created
  └── hls_url = https://cdn.example.com/hls/<video_id>/master.m3u8
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/videos/upload/` | Upload original video |
| `GET` | `/api/v1/videos/<id>/status/` | Poll encoding status |
| `POST` | `/api/v1/videos/<id>/retry_encoding/` | Retry failed encoding |
| `GET` | `/api/v1/videos/` | List all videos |
| `DELETE` | `/api/v1/videos/<id>/` | Delete video + R2 files |

---

## Useful Commands

```bash
# Check Celery task queue
python check_celery_queue.py

# Manually upload already-encoded HLS to R2 (emergency)
python manual_r2_upload.py

# Verify Supabase content sync
python verify_content_media_sync.py
```

---

## Documentation

Extended guides are in the [`docs/`](docs/) folder:

- [Architecture Summary](docs/ARCHITECTURE_SUMMARY.md)
- [Adaptive Bitrate Guide](docs/ADAPTIVE_BITRATE_GUIDE.md)
- [Django Setup](docs/DJANGO_PROJECT_SETUP.md)
- [Supabase Setup](docs/SUPABASE_SETUP.md)
- [Migration Guide](docs/MIGRATION_GUIDE.md)
- [VPS Provider Comparison](docs/VPS_PROVIDER_COMPARISON.md)
