#!/usr/bin/env python
"""
Check Celery task queue and active tasks
"""
import os
import redis
import json
from celery import Celery

# Read .env file
env_file = 'd:\\OTT App\\OTT-Backend\\.env'
env_vars = {}

if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

# Get Redis connection
CELERY_BROKER_URL = env_vars.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
print(f"📍 Redis URL: {CELERY_BROKER_URL}")

try:
    r = redis.from_url(CELERY_BROKER_URL)
    r.ping()
    print("✅ Connected to Redis")
except Exception as e:
    print(f"❌ Failed to connect to Redis: {e}")
    exit(1)

# Get all keys in Redis
try:
    keys = r.keys('*')
    print(f"\n📊 Redis Keys ({len(keys)} total):")
    for key in keys[:20]:  # Show first 20
        key_str = key.decode() if isinstance(key, bytes) else key
        key_type = r.type(key).decode() if isinstance(r.type(key), bytes) else r.type(key)
        value_len = r.strlen(key) if key_type == 'string' else r.llen(key) if key_type == 'list' else '?'
        print(f"   [{key_type:6}] {key_str}")
        
except Exception as e:
    print(f"❌ Error querying Redis: {e}")
    exit(1)

print("\n✅ Redis check completed")
