#!/usr/bin/env python
"""
Check status of recent Celery tasks
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
CELERY_BROKER_URL = env_vars.get('CELERY_BROKER_URL', 'redis://redis:6379/0')

try:
    r = redis.from_url(CELERY_BROKER_URL)
    r.ping()
except Exception as e:
    print(f"❌ Failed to connect to Redis: {e}")
    exit(1)

# Get all task metadata keys
task_keys = r.keys('celery-task-meta-*')
print(f"📊 Celery Task Status ({len(task_keys)} tasks):\n")

for task_key in sorted(task_keys, reverse=True):
    task_id = task_key.decode().replace('celery-task-meta-', '')
    task_data = r.get(task_key)
    
    if task_data:
        try:
            task_info = json.loads(task_data.decode())
            status = task_info.get('status', 'UNKNOWN')
            result = task_info.get('result', {})
            
            print(f"   Task ID: {task_id}")
            print(f"   Status: {status}")
            
            if status == 'FAILURE':
                print(f"   Error: {result}")
            elif status == 'SUCCESS':
                print(f"   Result: {str(result)[:100]}")
                
            print()
        except:
            print(f"   Task ID: {task_id} (unparseable)")
            print()

print("✅ Task check completed")
