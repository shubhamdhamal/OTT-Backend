# Django Project Setup Guide

The setup script requires a Django project structure with `manage.py` at the root of the OTT-Backend directory. You have two options:

## Option 1: Use Docker (Recommended for Production)

Docker will set up the entire Django project + PostgreSQL automatically:

```bash
docker-compose up -d
```

This will:
- Create the Django project container
- Set up PostgreSQL database
- Run migrations automatically
- Start the backend server on port 8000

**Verify it's running:**
```bash
docker-compose ps
```

**Access logs:**
```bash
docker-compose logs -f web
```

---

## Option 2: Manual Setup (For Development)

If you prefer to run Django manually on your machine:

### Step 1: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### Step 2: Create Django Project

```bash
pip install Django==4.2.0
django-admin startproject ott_backend .
```

This will create:
```
OTT-Backend/
├── ott_backend/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── hls_streaming/
```

### Step 3: Configure Django Settings

Edit `ott_backend/settings.py`:

**Add to INSTALLED_APPS:**
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'hls_streaming',  # ← Add this
]
```

**Add middleware (if not already there):**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # ← Add this
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware
]
```

**Configure CORS:**
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
```

**Configure database (from .env):**
```python
import os
from dotenv import load_dotenv

load_dotenv()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

**Add R2 storage configuration:**
```python
# Cloudflare R2 Configuration
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
R2_ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
```

### Step 4: Configure URLs

Edit `ott_backend/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('hls_streaming.urls')),
]
```

### Step 5: Run Setup Script

Now you can run the setup script:

**Windows:**
```powershell
.\hls_setup.bat
```

**Linux/macOS:**
```bash
bash hls_setup.sh
```

---

## Verifying Setup

After running the setup script, verify everything works:

### Check Database Connection
```bash
python manage.py dbshell
```

### Test R2 Connection
```bash
python manage.py shell
>>> from hls_streaming.r2_service import get_r2_service_from_settings
>>> from django.conf import settings
>>> r2 = get_r2_service_from_settings(settings)
>>> print("✅ R2 Connected!" if r2 else "❌ R2 Failed")
>>> exit()
```

### Run Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

Then access:
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/

---

## Troubleshooting

**Error: `manage.py not found`**
- You haven't created the Django project yet
- Follow Option 1 (Docker) or Option 2 (Manual) above

**Error: `ModuleNotFoundError: No module named 'django'`**
- Virtual environment not activated
- Run: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)

**Error: `ModuleNotFoundError: No module named 'hls_streaming'`**
- Django doesn't know about the app
- Add `'hls_streaming'` to `INSTALLED_APPS` in `settings.py`

**Error: Database connection failed**
- Check PostgreSQL is running
- Verify `.env` has correct DB credentials
- For Supabase: Use host like `db.rejehvyigxzxbyrpfrsy.supabase.co`

**Error: R2 connection test failed**
- Check R2 credentials in `.env`
- Verify R2 bucket exists in Cloudflare dashboard
- Test credentials with: `aws s3 --endpoint-url https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com ls`

---

## Next Steps

1. ✅ Create Django project (Option 1 or 2)
2. ✅ Run setup script
3. ✅ Test video upload: See QUICK_REFERENCE.md
4. ✅ Deploy to VPS: See VPS_SPECIFICATIONS.md
