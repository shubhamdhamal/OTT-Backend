# OTT Backend - HLS Streaming Service

Complete Django backend for HLS video streaming with adaptive bitrate encoding.

## Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg with libx265 support (H.265 codec)
- PostgreSQL 12+
- Redis 6+

### Installation

1. **Clone and setup**
   ```bash
   cd OTT-Backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r HLS_REQUIREMENTS.txt
   ```

2. **Configure Django**
   - Copy `.env.example` to `.env`
   - Update environment variables in `.env`
   - Add HLS app to Django `INSTALLED_APPS` in settings.py:
     ```python
     INSTALLED_APPS = [
         # ...
         'hls_streaming',
     ]
     ```

3. **Run migrations**
   ```bash
   python manage.py makemigrations hls_streaming
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Start services**
   ```bash
   # Terminal 1: Django development server
   python manage.py runserver
   
   # Terminal 2: Celery worker (for async encoding)
   celery -A ott_backend worker -l info
   
   # Terminal 3 (optional): Celery Beat (for scheduled tasks)
   celery -A ott_backend beat -l info
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## API Endpoints

### Video Upload
```
POST /api/v1/videos/upload/
Content-Type: multipart/form-data

Form data:
- video_file: <file>
- title: "Video Title"
- description: "Optional description"
```

### Check Encoding Status
```
GET /api/v1/videos/{video_id}/encoding_status/
```

Response:
```json
{
  "video_id": "video_123",
  "title": "Video Title",
  "status": "uploading|encoding|completed|failed",
  "encoding_status": "pending|encoding|completed|failed",
  "progress": 0-100,
  "master_playlist_url": "https://...",
  "estimated_size_mb": 750.5,
  "renditions": [...]
}
```

### Get Master Playlist
```
GET /api/v1/videos/{video_id}/playlist/
```

### Download Playlist File
```
GET /api/v1/videos/{video_id}/download_playlist/
```

### Retry Failed Encoding
```
POST /api/v1/videos/{video_id}/retry_encoding/
```

## HLS Streaming Details

### Supported Renditions
- **480p** (854×480 @ 800 kbps)
- **720p** (1280×720 @ 1400 kbps)

### Codec Support
- **Primary**: H.265 (HEVC) - 40% better compression
- **Fallback**: H.264 - Universal compatibility
- **Audio**: AAC @ 128 kbps

### Target File Size
700-850 MB per video with quality preservation

## Configuration

See `HLS_DJANGO_SETTINGS_CONFIG.py` for detailed settings explanation.

Key settings to customize:
- `HLS_OUTPUT_DIR`: Where encoded videos are stored
- `HLS_CDN_BASE_URL`: CDN URL for serving videos
- `CELERY_BROKER_URL`: Redis connection for task queue
- `MEDIA_ROOT`: User upload directory

## Validation

Run system validation:
```bash
python hls_validate.py
```

This checks:
- Python version
- FFmpeg installation
- Redis connectivity
- Django configuration
- Required directories

## Systemd Service (Production)

Create `/etc/systemd/system/ott-backend.service`:
```ini
[Unit]
Description=OTT Backend Django Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/ott-backend
Environment="PATH=/opt/ott-backend/venv/bin"
ExecStart=/opt/ott-backend/venv/bin/gunicorn ott_backend.wsgi:application --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ott-backend
sudo systemctl start ott-backend
```

## Monitoring

Check Celery tasks:
```bash
celery -A ott_backend inspect active
celery -A ott_backend inspect stats
```

View logs:
```bash
tail -f /var/log/hls_streaming.log
```

## Database Backup

```bash
pg_dump -U postgres ott_backend > backup.sql
```

Restore:
```bash
psql -U postgres ott_backend < backup.sql
```

## Troubleshooting

### FFmpeg not found
```bash
# Install FFmpeg
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Redis connection error
```bash
# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Database connection error
Update `.env` with correct PostgreSQL credentials

### Encoding timeout
Increase timeout in task settings or optimize video codec settings

## Production Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `SECRET_KEY` securely
- [ ] Use PostgreSQL (not SQLite)
- [ ] Set up Redis for Celery
- [ ] Configure CORS_ALLOWED_ORIGINS
- [ ] Set up HTTPS/SSL
- [ ] Configure email backend
- [ ] Set up log rotation
- [ ] Configure backup strategy
- [ ] Monitor disk space for HLS output
- [ ] Set up health checks
- [ ] Configure load balancer if needed

## License

Same as OTT Platform

## Support

For issues or questions, contact the development team.
