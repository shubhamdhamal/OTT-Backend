# Supabase PostgreSQL Integration Guide

## ✅ Yes, You Can Use Supabase!

Perfect choice! Supabase PostgreSQL works seamlessly with Django. Here's everything you need to know:

---

## 🎯 Setup Steps

### Step 1: Get Your Supabase Password

In Supabase dashboard:
1. Go to **Project Settings → Database**
2. Click **Reset Database Password**
3. Copy the password (shows once, save it!)
4. Or use: **Project Settings → API → Connection String** (already has password)

### Step 2: Update Your `.env` File

```env
# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-supabase-password-here
DB_HOST=db.rejehvyigxzxbyrpfrsy.supabase.co
DB_PORT=5432
```

**That's it!** Django automatically handles the connection using these individual parameters.

### Step 3: Verify Connection

```bash
python manage.py shell

>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("SELECT version();")
>>> print(cursor.fetchone())

# Should print something like:
# ('PostgreSQL 14.1 on x86_64-pc-linux-gnu...')
```

---

## 📊 Connection Methods Compared

### Method 1: Individual Parameters ✅ RECOMMENDED
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db.rejehvyigxzxbyrpfrsy.supabase.co
DB_PORT=5432
```

**Advantages:**
- ✅ No extra dependencies needed
- ✅ Works natively with Django
- ✅ Clear and explicit
- ✅ Easiest to debug

**Django settings.py:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
```

### Method 2: Connection String (Alternative)
```env
DATABASE_URL=postgresql://postgres:password@db.rejehvyigxzxbyrpfrsy.supabase.co:5432/postgres
```

**Requires:** `pip install dj-database-url`

**Django settings.py:**
```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}
```

**⚠️ Not recommended** (extra dependency, less explicit)

---

## 🔐 Getting Your Supabase Connection Details

### Option A: From Dashboard
1. Supabase → Project → Settings → Database
2. Look for "Connection info"
3. Copy individual values:
   - Host: `db.rejehvyigxzxbyrpfrsy.supabase.co`
   - Port: `5432`
   - Database: `postgres`
   - User: `postgres`
   - Password: (reset if needed)

### Option B: From Connection String
1. Supabase → Project → Settings → Database
2. Click "URI" or "Connection string"
3. Copy the full string: `postgresql://postgres:PASSWORD@HOST:5432/postgres`
4. Extract the parts:
   ```
   postgresql://postgres:PASSWORD@db.rejehvyigxzxbyrpfrsy.supabase.co:5432/postgres
                └─ user  └─password └─ host                        └port └─database
   ```

---

## ✨ Your Exact Configuration

Use this exact configuration for YOUR Supabase instance:

```env
# ============================================================================
# DATABASE - SUPABASE POSTGRESQL
# ============================================================================
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=YOUR_SUPABASE_PASSWORD_HERE
DB_HOST=db.rejehvyigxzxbyrpfrsy.supabase.co
DB_PORT=5432
```

**Where to get the password:**
1. Go to Supabase Dashboard
2. Project Settings → Database
3. Click "Reset Database Password"
4. Save the password shown

---

## 🚀 Testing Connection

### Test 1: Django Shell
```bash
python manage.py shell

>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("SELECT 1")
>>> print("✅ Connected to Supabase!")
```

### Test 2: Migrations
```bash
python manage.py migrate

# Should show:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, ...
# Running migrations:
#   ...
# ✅ if all migrations complete successfully
```

### Test 3: Create Superuser
```bash
python manage.py createsuperuser

# Follow prompts - creates user in Supabase database
```

### Test 4: Check Data in Supabase UI
1. Supabase Dashboard → Project
2. Go to **SQL Editor**
3. Run: `SELECT * FROM auth_user;`
4. Should see your superuser created!

---

## 🆚 Supabase vs Local PostgreSQL

| Feature | Supabase | Local PostgreSQL |
|---------|----------|-----------------|
| **Setup** | 2 minutes | 5+ minutes |
| **Maintenance** | ✅ None (managed) | ⚠️ You manage it |
| **Backups** | ✅ Automatic daily | ⚠️ Manual |
| **SSL/Security** | ✅ Encrypted | ⚠️ Manual SSL |
| **Remote access** | ✅ Yes (secure) | ⚠️ Difficult |
| **Cost** | Free tier available | ✅ $0 (your computer) |
| **Uptime SLA** | 99.9% | Depends on your PC |
| **Best for** | Production | Development |

---

## ⚠️ Important Notes

### 1. Connection Pooling (Optional but Recommended)
Supabase uses PgBouncer. If you hit connection limits:

```env
# Use connection pooler (Supabase PgBouncer)
DB_HOST=db.rejehvyigxzxbyrpfrsy.supabase.co  # Direct
# OR
DB_HOST=db.rejehvyigxzxbyrpfrsy-pooler.supabase.co  # Pooled (recommended for Django)
```

**Pooled is better for Django** (handles many small connections efficiently)

### 2. Database Backups
✅ Supabase backs up automatically (daily, kept 7 days)
- Dashboard → Backups
- Can restore anytime

### 3. Real-time Updates (Optional)
Supabase offers real-time subscriptions via PostgREST - not needed for your HLS backend, but available if you want to add live features later.

### 4. Database Extensions
Already enabled:
- ✅ PostGIS (for geographic data)
- ✅ UUID (for IDs)
- ✅ JWT
- ✅ Full-text search

No additional setup needed!

---

## 🐛 Troubleshooting

### Error: "Could not connect to server"
```python
# Check error:
python manage.py shell
# If fails with connection error:

# 1. Verify .env has correct values
cat .env

# 2. Test network access
ping db.rejehvyigxzxbyrpfrsy.supabase.co

# 3. Check Supabase dashboard is working
# Go to https://app.supabase.com - can you login?

# 4. Review Supabase logs
# Dashboard → Logs → Database
```

### Error: "FATAL: PAM authentication failed"
```
Cause: Wrong password or user
Solution:
  1. Reset password in Supabase Dashboard
  2. Update DB_PASSWORD in .env
  3. Try again
```

### Error: "Remaining connection slots are reserved..."
```
Cause: Too many connections
Solution:
  1. Switch to pooler: db....-pooler.supabase.co
  2. Check for connection leaks: ps aux | grep postgres
  3. Restart Django service
```

### Slow Connections from VPS
```
Cause: Network latency
Solutions:
  1. Use Supabase region closest to your VPS
  2. Monitor: Supabase Dashboard → Logs
  3. Consider: VPS in same region as Supabase

Best regions:
- Frankfurt (Europe)
- Singapore (Asia)
- US East 1 (Americas)
```

---

## 📈 Scaling with Supabase

### Free Tier
```
Storage: 500 MB
Connections: 10
Cost: $0
Best for: Development, testing
```

### Pro Tier ($25/month)
```
Storage: 8 GB
Connections: 100
Cost: $25/month
Best for: Small productions
```

### Enterprise
```
Custom storage/connections
Custom pricing
Best for: Large scale
```

**Your HLS backend usage:**
- Database size: Small (~100MB for 1000 videos)
- Connections: Low (1-2 per upload)
- Fine with Free or Pro tier ✅

---

## 🔗 Connection String Formats

### PostgreSQL Native
```
postgresql://postgres:PASSWORD@db.rejehvyigxzxbyrpfrsy.supabase.co:5432/postgres
```

### psql CLI
```bash
psql postgresql://postgres:PASSWORD@db.rejehvyigxzxbyrpfrsy.supabase.co:5432/postgres
```

### Python psycopg2
```python
import psycopg2

conn = psycopg2.connect(
    host="db.rejehvyigxzxbyrpfrsy.supabase.co",
    database="postgres",
    user="postgres",
    password="PASSWORD",
    port=5432
)
```

### Django (what we're using)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'PASSWORD',
        'HOST': 'db.rejehvyigxzxbyrpfrsy.supabase.co',
        'PORT': '5432',
    }
}
```

---

## 🎯 Step-by-Step Setup (Complete)

### 1. Get Password
```
Supabase Dashboard → Project Settings → Database → "Reset Database Password"
Save the password
```

### 2. Update .env
```bash
# Edit your .env file:
nano .env

# Add/Update these lines:
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD_HERE
DB_HOST=db.rejehvyigxzxbyrpfrsy.supabase.co
DB_PORT=5432
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Verify in Supabase UI
```
Supabase Dashboard → SQL Editor
SELECT * FROM auth_user;
# Should show your superuser
```

### 6. Done! 🎉
Everything works just like local PostgreSQL!

---

## 💡 Benefits You Now Have

✅ **Automatic backups** (daily, 7 days retention)
✅ **99.9% uptime SLA** (managed by Supabase/Google Cloud)
✅ **Zero maintenance** (they manage PostgreSQL patches)
✅ **Accessible from anywhere** (VPS can connect from any region)
✅ **Free tier** (if under 500MB storage)
✅ **Instant scaling** (upgrade with one click)
✅ **Security** (SSL encrypted, protected)

---

## 📚 Quick Reference

```bash
# Test connection
python manage.py migrate

# Connect to database
psql postgresql://postgres:PASSWORD@db.rejehvyigxzxbyrpfrsy.supabase.co:5432/postgres

# View logs
Supabase Dashboard → Logs → Database

# Check connections
SELECT datname, usename, count(*) FROM pg_stat_activity GROUP BY datname, usename;

# Monitor queries
Supabase Dashboard → Logs → Real-time
```

---

## Summary

✅ **Use individual parameters** (DB_HOST, DB_PORT, DB_USER, etc.) - not connection string
✅ **No extra dependencies** - Django handles it natively
✅ **Works perfectly** for HLS backend
✅ **Much better than local** for production (backups, uptime, maintenance)
✅ **Easy to test** with psql command

**Your .env configuration:**
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=YOUR_SUPABASE_PASSWORD
DB_HOST=db.rejehvyigxzxbyrpfrsy.supabase.co
DB_PORT=5432
```

You're all set! 🚀
