"""
Celery configuration for OTT Backend
Handles async video encoding and other long-running tasks
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ott_backend.settings')

app = Celery('ott_backend')

# Configure Celery to use Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Task routing configuration
app.conf.task_routes = {
    'hls_streaming.tasks.encode_video_to_hls': {'queue': 'video_encoding'},
}

# Task configuration
app.conf.task_track_started = True
app.conf.task_send_sent_event = True

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
