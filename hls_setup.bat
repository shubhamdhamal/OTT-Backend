@echo off
REM HLS Backend Setup Script for Windows (No Redis + R2)
REM Automates setup for synchronous encoding with R2 upload

setlocal enabledelayedexpansion

echo.
echo 🚀 Setting up HLS Streaming Backend (No Redis/Celery)...
echo.

REM Check Python version
python --version
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

REM Check FFmpeg installation
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo ❌ FFmpeg is required but not installed.
    echo    Download from: https://ffmpeg.org/download.html
    exit /b 1
)
echo ✅ FFmpeg found

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r HLS_REQUIREMENTS.txt

REM Create necessary directories
echo 📁 Creating directories...
if not exist "%TEMP%\hls_videos" mkdir "%TEMP%\hls_videos"
if not exist "%SystemDrive%\var\media" mkdir "%SystemDrive%\var\media"
if not exist "%SystemDrive%\var\log" mkdir "%SystemDrive%\var\log"

REM Check .env file
if not exist ".env" (
    echo ❌ .env file not found!
    echo    1. Copy .env.example to .env
    echo    2. Fill in your R2 credentials
    exit /b 1
)

REM Verify R2 credentials are configured
findstr /M "your-account-id" .env >nul
if not errorlevel 1 (
    echo ❌ R2 credentials not configured in .env
    echo    Update .env with your Cloudflare R2 credentials
    exit /b 1
)

echo ✅ Configuration files OK

REM Check if Django project exists
if not exist "manage.py" (
    echo ❌ manage.py not found!
    echo.
    echo You need to set up a Django project first.
    echo.
    echo Option 1 - Use Docker:
    echo    1. Make sure you have Docker installed
    echo    2. Run: docker-compose up -d
    echo.
    echo Option 2 - Create Django project manually:
    echo    1. Run: pip install Django==4.2.0
    echo    2. django-admin startproject ott_backend .
    echo    3. Copy hls_streaming/ app into the project
    echo    4. Add 'hls_streaming' to INSTALLED_APPS in settings.py
    echo.
    exit /b 1
)

REM Run migrations
echo 🗄️  Running database migrations...
python manage.py makemigrations hls_streaming 2>nul
python manage.py migrate
if errorlevel 1 (
    echo ❌ Database migration failed
    exit /b 1
)

REM Create superuser
echo 👤 Creating superuser...
python manage.py createsuperuser

REM Collect static files
echo 📊 Collecting static files...
python manage.py collectstatic --noinput

REM Test R2 connection
echo 🔗 Testing R2 connection...
(
    echo from hls_streaming.r2_service import get_r2_service_from_settings
    echo from django.conf import settings
    echo try:
    echo     r2 = get_r2_service_from_settings(settings^
    echo     if r2:
    echo         print("✅ R2 connection successful!"^
    echo     else:
    echo         print("❌ R2 connection failed. Check .env credentials"^
    echo         exit(1^
    echo except Exception as e:
    echo     print(f"❌ R2 connection error: {str(e^}^"^
    echo     exit(1^
) | python manage.py shell

if errorlevel 1 (
    echo ⚠️  R2 test failed - check your R2 credentials in .env
)

REM Display important notes
echo.
echo ⚠️  IMPORTANT NOTES:
echo    • Encoding is SYNCHRONOUS (blocks for 15-30 minutes per video)
echo    • No Celery workers or Redis needed
echo    • Configure HTTP timeout: 1800+ seconds at load balancer
echo    • Temp directory: %TEMP%\hls_videos (should have 50GB+ free)
echo.

REM Start server
echo 🌐 Starting Django development server...
echo    Server: http://127.0.0.1:8000
echo    Admin:  http://127.0.0.1:8000/admin
echo.
echo ✅ Setup complete! Backend is ready.
echo.
echo To test uploading a video:
echo   curl -X POST http://localhost:8000/api/v1/videos/upload/ ^
echo     -H "Authorization: Token YOUR_TOKEN" ^
echo     -F "video_file=@video.mp4" ^
echo     -F "title=Test Video"
echo.

python manage.py runserver
