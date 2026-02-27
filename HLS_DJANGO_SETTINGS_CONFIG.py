"""
Django Settings Configuration for OTT Backend with HLS Streaming
NO Redis/Celery - Synchronous encoding with R2 storage
Add these settings to your Django settings.py
"""

# ============================================================================
# HLS STREAMING CONFIGURATION
# ============================================================================

# HLS Output Directory (temporary, files deleted after R2 upload)
HLS_OUTPUT_DIR = '/tmp/hls_videos'  # Temp location during encoding

# HLS CDN Base URL (optional - for local serving fallback)
HLS_CDN_BASE_URL = 'https://cdn.example.com/videos'  # Update with your CDN URL

# ============================================================================
# INSTALLED APPS
# ============================================================================
# Add 'hls_streaming' to your INSTALLED_APPS:

INSTALLED_APPS = [
    # ... existing apps ...
    'rest_framework',
    'corsheaders',
    'hls_streaming',
]

# ============================================================================
# CLOUDFLARE R2 STORAGE CONFIGURATION
# ============================================================================
# For HLS segments, playlists, and other media

R2_ACCOUNT_ID = 'your-account-id'  # Get from Cloudflare R2
R2_ACCESS_KEY_ID = 'your-access-key-id'  # Get from Cloudflare R2
R2_SECRET_ACCESS_KEY = 'your-secret-access-key'  # Get from Cloudflare R2
R2_BUCKET_NAME = 'ott-videos'  # Name of your R2 bucket
R2_REGION = 'auto'  # R2 region (usually 'auto')

# ============================================================================
# NO CELERY/REDIS CONFIGURATION
# ============================================================================
# Encoding is now synchronous!
# Remove Celery configuration if present.
# Video uploads will block until encoding completes.
#
# For high-traffic deployments, consider:
# - Using a dedicated encoding server with longer timeouts
# - Implementing webhook-based status checks
# - Running upload endpoint on separate worker with higher timeout
#
# DO NOT add:
# - CELERY_BROKER_URL
# - CELERY_RESULT_BACKEND
# - Redis configuration
#
# This simplifies infrastructure significantly!

# ============================================================================
# REST FRAMEWORK CONFIGURATION
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://yourdomain.com",
    "https://admin.yourdomain.com",
]

# ============================================================================
# MEDIA FILES CONFIGURATION
# ============================================================================
# For temporary storage during upload/encoding

MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/media'

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/hls_streaming.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'hls_streaming': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

# ============================================================================
# DEPLOYMENT NOTES
# ============================================================================
#
# SYNCHRONOUS ENCODING:
# - Video uploads will block until encoding completes
# - Large videos (>500MB) may take 10-30 minutes
# - Configure appropriate HTTP request timeout (e.g., 5 minutes via load balancer)
# - Consider separate encoding server or multiple workers
#
# R2 STORAGE:
# - All HLS files (segments, playlists) are uploaded to R2 after encoding
# - Local HLS files are deleted after successful R2 upload
# - Save significant disk space on server
#
# BENEFITS:
# ✅ No Redis required
# ✅ No Celery workers needed
# ✅ Simpler infrastructure
# ✅ No background job complexity
# ✅ R2 $0.02/GB storage (very cheap)
#
# TRADEOFFS:
# ⚠️  Upload endpoint blocks during encoding
# ⚠️  FFmpeg must be installed on backend server
# ⚠️  Large video encoding requires significant CPU/RAM
#
# RECOMMENDATIONS:
# 1. Set HTTP timeouts to 30+ minutes at load balancer
# 2. Monitor disk space in /tmp/hls_videos during encoding
# 3. Use SSD for temp storage for faster encoding
# 4. Consider horizontal scaling with multiple encoding servers
# 5. Join Discord for support: https://discord.gg/ott-community

