# Admin Portal ↔ Django Backend Integration

## Overview

The admin portal now sends video files directly to the Django backend for HLS encoding. Here's the complete flow:

```
Admin Portal → Form submission → Backend API (/api/v1/videos/upload/)
                                     ↓
                            FFmpeg encoding locally
                                     ↓
                             Upload to R2 storage
                                     ↓
                            Delete temp files
                                     ↓
                        Database updated with URLs
                                     ↓
                        Admin Portal redirects to content list
```

---

## Setup Instructions

### Step 1: Backend Configuration

Ensure Django backend is running:

```bash
cd OTT-Backend
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows

python manage.py runserver 0.0.0.0:8000
```

**Verify:**
```bash
curl -X GET http://localhost:8000/api/v1/videos/
```

### Step 2: Admin Portal Configuration

Add backend URL to `.env.local`:

```env
# .env.local
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000/api/v1
```

Start the admin portal:

```bash
cd ott-admin-portal
npm install  # If not done yet
npm run dev
```

**Access:** http://localhost:3000/admin/login

### Step 3: CORS Configuration (Django)

Verify CORS settings in `ott_backend/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # ✅ Admin portal
    "http://localhost:8000",      # ✅ Django admin
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
```

If you changed the admin portal port, add it:
```python
CORS_ALLOWED_ORIGINS.append("http://localhost:YOUR_PORT")
```

Then restart Django.

---

## Complete Upload Flow

### 1. Admin Portal User Action

```
✅ Fill form with content details
✅ Select video file (main_video_url)
✅ Select thumbnail (optional)
✅ Select trailer (optional)
✅ Click "Publish Content" button
```

### 2. Form Submission (Browser)

- Validates required fields
- Collects all form data
- Creates FormData with files
- Sends to backend API: `POST /api/v1/videos/upload/`

```typescript
// Example payload
FormData {
  content_type_id: 1,
  title: "My Video",
  description: "...",
  main_video_url: File(video.mp4),  // ← Actual file
  thumbnail_url: File(thumbnail.jpg),
  status: "published",
  ...
}
```

### 3. Backend Processing

**Route:** `POST /api/v1/videos/upload/`

```
Step 1: Receive video file
Step 2: Create HLSPlaylist record in database (status: 'uploading')
Step 3: Encode video with FFmpeg (H.264 480p, H.265 720p)
Step 4: Generate master.m3u8 playlist
Step 5: Upload all files to R2 (boto3)
Step 6: Update database with R2 URLs
Step 7: Delete temp files from /tmp/hls_videos
Step 8: Return master playlist URL to frontend
```

**Response:**
```json
{
  "success": true,
  "master_playlist_url": "https://pub-xxx.r2.dev/videos/video_123/master.m3u8",
  "r2_uploaded": true,
  "status": "completed"
}
```

### 4. Admin Portal Success

```
✅ Shows success message
✅ Saves content to Supabase with R2 URLs
✅ Redirects to content list
✅ Video is immediately available for streaming
```

---

## Monitoring Encoding Progress

### From Admin Portal Dashboard

```
Content List → Click on content item → View encoding status
Status options:
  - ⏳ uploading (file received, encoding in progress)
  - ✅ completed (ready to stream)
  - ⚠️ failed (check backend logs)
```

### From Backend Logs

```bash
# Terminal 1: Watch Django server logs
python manage.py runserver 0.0.0.0:8000

# Look for lines like:
# [video_123] Encoding started (size: 450MB)
# [video_123] Encoding completed in 15m 32s
# [video_123] Uploading to R2...
# [video_123] R2 upload complete
```

### From Database

```bash
# Check encoding status in Supabase
SELECT id, title, status, r2_uploaded, views, created_at 
FROM contents 
ORDER BY created_at DESC 
LIMIT 10;

# Expected:
# id                           | title      | status    | r2_uploaded | views | created_at
# content_1708888123_abc123    | My Video   | completed | true        | 0     | 2026-02-26
```

---

## Error Handling

### Issue: "Backend is not responding"

**Solution:**
1. Check Django is running: `http://localhost:8000/admin`
2. Check CORS settings in `ott_backend/settings.py`
3. Check .env.local has correct backend URL

```env
# Correct:
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000/api/v1

# Wrong:
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000  # Missing /api/v1
```

### Issue: "CORS error" in browser console

**Solution:**
Add admin portal URL to Django CORS settings:

```python
# ott_backend/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Your admin portal port
    "http://localhost:8000",
]
```

### Issue: "Encoding takes 30+ minutes"

**This is normal!** For large videos (500MB+), encoding can take:
- 480p H.264: ~5-10 minutes
- 720p H.265: ~15-25 minutes
- Total: 20-35 minutes

**Timeout configuration needed at production (load balancer):**
```
HTTP Request Timeout: 1800+ seconds (30 minutes)
Keep-Alive: enabled
```

### Issue: "Disk space error"

**Usually means `/tmp` is full:**

```bash
# Check disk space
df -h /tmp

# Clear old HLS files
rm -rf /tmp/hls_videos/*

# Or on Windows:
rmdir /S C:\Users\YourUser\AppData\Local\Temp\hls_videos
```

**Requirement:** 50GB+ free space recommended

### Issue: "FFmpeg not found"

**Solution:**
```bash
# Linux/Ubuntu
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows (already installed, verify)
ffmpeg -version
```

---

## Testing the Integration

### Test 1: Simple Upload

1. Go to http://localhost:3000/admin/login
2. Login with admin credentials
3. Navigate to Content → Upload Content
4. Fill form:
   - Title: "Test Video"
   - Description: "Test"
   - Content Type: (select any)
   - Upload a small video (< 50MB)
5. Click "Publish Content"

**Expected:**
- ✅ Backend receives file
- ✅ Encoding starts
- ✅ Progress shows in console
- ✅ Redirect to content list after 1-2 minutes
- ✅ Video is available at R2 URL

### Test 2: Check Encoded Files

```bash
# List files in R2
# Via browser: https://dash.cloudflare.com > R2

# Should see structure:
# ott-platform-media/
#   └── videos/
#       └── content_123456/
#           ├── master.m3u8
#           ├── 480p_playlist.m3u8
#           ├── 720p_playlist.m3u8
#           ├── segment_480p_00001.ts
#           └── segment_720p_00001.ts
```

### Test 3: Stream Encoded Video

1. Get the content ID from the admin portal
2. Access the video via any HLS player:
   ```
   https://pub-xxx.r2.dev/videos/{content_id}/master.m3u8
   ```

**Or test in Flutter app:**
```dart
// Should automatically stream encoded video
// Player switches quality based on network speed
```

---

## Production Deployment

### Configuration

**1. Update backend URL in admin portal:**

```env
# .env.local (production)
NEXT_PUBLIC_BACKEND_API_URL=https://api.yourdomain.com/api/v1
```

**2. Update CORS in Django:**

```python
# settings.py (production)
CORS_ALLOWED_ORIGINS = [
    "https://admin.yourdomain.com",
    "https://yourdomain.com",
    "https://api.yourdomain.com",
]
```

**3. Configure load balancer timeout:**

```
# Nginx example
proxy_connect_timeout 1800s;
proxy_send_timeout 1800s;
proxy_read_timeout 1800s;

# HAProxy example
timeout connect 1800000
timeout client 1800000
timeout server 1800000
```

**4. Monitor disk space:**

```bash
# Set up cron job to clean old files weekly
# crontab -e
0 2 * * 0 rm -rf /tmp/hls_videos/*
```

---

## API Reference

### Upload Video

**Endpoint:** `POST /api/v1/videos/upload/`

**Request:**
```http
POST /api/v1/videos/upload/ HTTP/1.1
Content-Type: multipart/form-data

title=My Video
description=A test video
content_type_id=1
main_video_url=[binary file]
thumbnail_url=[binary file]
```

**Response:**
```json
{
  "success": true,
  "master_playlist_url": "https://pub-xxx.r2.dev/videos/video_123/master.m3u8",
  "segments_url": "https://pub-xxx.r2.dev/videos/video_123/",
  "r2_uploaded": true,
  "status": "completed",
  "duration_minutes": 45,
  "file_size_mb": 450
}
```

**Errors:**
```json
{
  "error": "Video file not found",
  "status": 400
}
```

---

## Troubleshooting Checklist

- [ ] Django backend running: `python manage.py runserver`
- [ ] Admin portal running: `npm run dev`
- [ ] `.env.local` has correct `NEXT_PUBLIC_BACKEND_API_URL`
- [ ] Django CORS includes `http://localhost:3000`
- [ ] R2 bucket exists and credentials are correct
- [ ] `/tmp` has 50GB+ free space
- [ ] FFmpeg is installed: `ffmpeg -version`
- [ ] PostgreSQL is reachable (database migrations passed)
- [ ] Browser DevTools shows no CORS errors
- [ ] Check Django logs for encoding errors

---

## Files Modified

1. **Backend:**
   - `ott_backend/urls.py`: Added `/api/v1/` route
   - `ott_backend/settings.py`: CORS configuration, R2 settings

2. **Admin Portal:**
   - `app/api/admin/content/upload/route.ts`: Now calls Django backend
   - `app/admin/content/upload/page.tsx`: Updated form to use FormData
   - `.env.local`: Added `NEXT_PUBLIC_BACKEND_API_URL`

---

## Next Steps

1. ✅ Test upload with small video (< 50MB)
2. ✅ Test upload with large video (> 500MB)
3. ✅ Verify R2 files exist
4. ✅ Stream video from Flutter app
5. ✅ Deploy to production VPS
6. ✅ Configure custom domain + SSL
7. ✅ Set up monitoring and alerts
