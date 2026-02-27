#!/usr/bin/env python
"""
Extract content_id from a successful Celery task result
"""
import os
import redis
import json

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

try:
    r = redis.from_url(CELERY_BROKER_URL)
    r.ping()
except Exception as e:
    print(f"❌ Failed to connect to Redis: {e}")
    exit(1)

# Get the most recent successful task
task_keys = r.keys('celery-task-meta-*')
most_recent = None

for task_key in task_keys:
    task_data = r.get(task_key)
    if task_data:
        try:
            task_info = json.loads(task_data.decode())
            # Look for successful tasks with result containing video_id
            if task_info.get('status') == 'SUCCESS' and isinstance(task_info.get('result'), dict):
                if 'master_playlist_url' in task_info.get('result', {}):
                    video_id = task_info.get('result', {}).get('video_id')
                    if video_id:
                        most_recent = {
                            'key': task_key.decode(),
                            'id': video_id,
                            'url': task_info.get('result', {}).get('master_playlist_url')
                        }
        except:
            pass

if most_recent:
    print(f"✅ Latest successful Celery task:")
    print(f"   Task Key: {most_recent['key']}")
    print(f"   Video ID: {most_recent['id']}")
    print(f"   Master URL: {most_recent['url']}")
    print(f"\n🔍 Now checking what content_id this video has in Supabase...")
    
    # Connect to Supabase
    from supabase import create_client
    
    SUPABASE_URL = env_vars.get('SUPABASE_URL')
    SUPABASE_KEY = env_vars.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Search for this master URL in content_media
        response = supabase.table('content_media').select('*').eq('file_url', most_recent['url']).execute()
        
        if response.data:
            entry = response.data[0]
            print(f"\n📊 Found in Supabase:")
            print(f"   content_id: {entry.get('content_id')}")
            print(f"   media_type: {entry.get('media_type')}")
            print(f"   is_primary: {entry.get('is_primary')}")
        else:
            print(f"\n❌ NOT found in Supabase!")
else:
    print("❌ No recent successful tasks found")
