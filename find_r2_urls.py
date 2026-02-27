#!/usr/bin/env python
"""
Search for R2 URLs in Supabase content_media (created by Celery task)
"""
import os
from supabase import create_client

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

# Get credentials
SUPABASE_URL = env_vars.get('SUPABASE_URL')
SUPABASE_KEY = env_vars.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase credentials not found")
    exit(1)

# Create client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Query ALL content_media (no limit)
try:
    response = supabase.table('content_media').select('*').execute()
    data = response.data
    
    print(f"📊 Searching for R2 URLs in {len(data)} content_media entries...\n")
    
    r2_entries = []
    for entry in data:
        file_url = entry.get('file_url', '')
        if 'r2.dev' in file_url or 'bdns.dev' in file_url or '.m3u8' in file_url:
            r2_entries.append(entry)
    
    if r2_entries:
        print(f"✅ Found {len(r2_entries)} R2/HLS entries:\n")
        for i, entry in enumerate(r2_entries, 1):
            print(f"   [{i}] content_id: {entry.get('content_id')}")
            print(f"       media_type: {entry.get('media_type')}")
            print(f"       file_url: {entry.get('file_url')}")
            print(f"       is_primary: {entry.get('is_primary')}")
            print(f"       created_at: {entry.get('created_at')}\n")
    else:
        print("❌ NO R2/HLS entries found!")
        print("\nThis means Celery tasks haven't saved content_media entries yet.")
        print("Possible reasons:")
        print("  1. Task is older than content_media entries (which are all demo videos)")
        print("  2. Task succeeded but Supabase insert failed silently")
        print("  3. content_id wasn't passed from admin portal to Celery task")
            
except Exception as e:
    print(f"❌ Failed to query: {e}")
    exit(1)

print("✅ Search completed")
