#!/usr/bin/env python
"""
Quick verification script to check Supabase content_media entries
"""
import os
from supabase import create_client

# Read .env file directly
env_file = 'd:\\OTT App\\OTT-Backend\\.env'
env_vars = {}

if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

# Get environment variables
SUPABASE_URL = env_vars.get('SUPABASE_URL')
SUPABASE_KEY = env_vars.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase credentials not found")
    print(f"   SUPABASE_URL: {SUPABASE_URL}")
    print(f"   SUPABASE_SERVICE_ROLE_KEY: {bool(SUPABASE_KEY)}")
    print(f"\n   Check .env file at: {env_file}")
    exit(1)

print(f"✅ Credentials found from .env")
print(f"   URL: {SUPABASE_URL[:50]}...")

# Create client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    exit(1)

# Query content_media table
try:
    response = supabase.table('content_media').select('*').limit(10).execute()
    data = response.data
    
    print(f"\n📊 content_media entries (last 10):")
    if not data:
        print("   (no entries found)")
    else:
        for i, entry in enumerate(data, 1):
            print(f"\n   [{i}] content_id: {entry.get('content_id')}")
            print(f"       media_type: {entry.get('media_type')}")
            print(f"       file_url: {entry.get('file_url')}")
            print(f"       is_primary: {entry.get('is_primary')}")
            print(f"       created_at: {entry.get('created_at')}")
            
except Exception as e:
    print(f"❌ Failed to query content_media: {e}")
    exit(1)

print("\n✅ Script completed successfully")
