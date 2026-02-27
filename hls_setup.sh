#!/bin/bash

# HLS Backend Setup Script for Linux (No Redis + R2)
# Automates setup for synchronous encoding with R2 upload
# Works with: Encode locally → Upload to R2 → Delete temp files

set -e

echo ""
echo "🚀 Setting up HLS Streaming Backend (No Redis/Celery)..."
echo ""

# Check Python version
echo "📦 Checking Python version..."
python3 --version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✅ Python version OK"
echo ""

# Check FFmpeg installation
echo "🎬 Checking FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is required but not installed."
    echo "   Install with: sudo apt-get install ffmpeg"
    exit 1
fi
echo "✅ FFmpeg found: $(ffmpeg -version | head -n 1)"
echo ""

# Check PostgreSQL
echo "🗄️  Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found."
    echo "   Make sure PostgreSQL server is running (local or Supabase)"
else
    echo "✅ PostgreSQL client found"
fi
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r HLS_REQUIREMENTS.txt
echo "✅ Dependencies installed"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /tmp/hls_videos
mkdir -p /var/media
mkdir -p /var/log
chmod 777 /tmp/hls_videos
chmod 777 /var/media
echo "✅ Directories created"
echo ""

# Check .env file
echo "⚙️  Checking configuration..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   1. Copy .env.example to .env"
    echo "   2. Fill in your R2 and database credentials"
    echo "      cp .env.example .env"
    exit 1
fi

# Verify R2 credentials are configured
if grep -q "your-account-id-here" .env || grep -q "R2_ACCOUNT_ID=$" .env; then
    echo "❌ R2 credentials not configured in .env"
    echo "   Update .env with your Cloudflare R2 credentials"
    exit 1
fi

echo "✅ Configuration files OK"
echo ""

# Check if Django project exists
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py not found!"
    echo ""
    echo "You need to set up a Django project first."
    echo ""
    echo "Option 1 - Use Docker:"
    echo "   1. Make sure you have Docker installed"
    echo "   2. Run: docker-compose up -d"
    echo ""
    echo "Option 2 - Create Django project manually:"
    echo "   1. Activate venv: source venv/bin/activate"
    echo "   2. Run: pip install Django==4.2.0"
    echo "   3. Then: django-admin startproject ott_backend ."
    echo "   4. Copy hls_streaming/ app into the project"
    echo "   5. Add 'hls_streaming' to INSTALLED_APPS in settings.py"
    echo ""
    exit 1
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations hls_streaming 2>/dev/null || true
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "❌ Database migration failed"
    exit 1
fi
echo "✅ Database migrations complete"
echo ""

# Create superuser
echo "👤 Creating superuser..."
python manage.py createsuperuser
echo ""

# Collect static files
echo "📊 Collecting static files..."
python manage.py collectstatic --noinput
echo "✅ Static files collected"
echo ""

# Test R2 connection
echo "🔗 Testing R2 connection..."
python manage.py shell << 'ENDPYTHON'
from hls_streaming.r2_service import get_r2_service_from_settings
from django.conf import settings
try:
    r2 = get_r2_service_from_settings(settings)
    if r2:
        print("✅ R2 connection successful!")
    else:
        print("❌ R2 connection failed. Check .env credentials")
        import sys
        sys.exit(1)
except Exception as e:
    print(f"❌ R2 connection error: {str(e)}")
    import sys
    sys.exit(1)
ENDPYTHON

if [ $? -ne 0 ]; then
    echo "❌ R2 test failed"
    exit 1
fi
echo ""

# Display important notes
echo "════════════════════════════════════════"
echo "⚠️  IMPORTANT NOTES:"
echo "════════════════════════════════════════"
echo ""
echo "• Encoding is SYNCHRONOUS (blocks for 15-30 minutes per video)"
echo "• No Celery workers or Redis needed"
echo "• Configure HTTP timeout: 1800+ seconds at load balancer"
echo "• Temp directory: /tmp/hls_videos (should have 50GB+ free)"
echo ""

# Start server
echo "🌐 Starting Django development server..."
echo "   Server: http://0.0.0.0:8000"
echo "   Admin:  http://0.0.0.0:8000/admin"
echo ""
echo "✅ Setup complete! Backend is ready."
echo ""
echo "To test uploading a video:"
echo "  curl -X POST http://localhost:8000/api/v1/videos/upload/ \\"
echo "    -H 'Authorization: Token YOUR_TOKEN' \\"
echo "    -F 'video_file=@video.mp4' \\"
echo "    -F 'title=Test Video'"
echo ""

python manage.py runserver 0.0.0.0:8000
