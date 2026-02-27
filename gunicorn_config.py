"""
Gunicorn configuration for OTT Backend
Optimized for long-running video upload requests
"""

import os

# Server socket
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', 3))
worker_class = 'sync'  # Use sync workers for file I/O
worker_connections = 100
max_requests = 1000
max_requests_jitter = 50

# Timeout settings (CRITICAL for large video uploads)
# Soft timeout: 30 minutes (1800 seconds)
timeout = int(os.getenv('GUNICORN_TIMEOUT', 3600))

# Keep-alive connections
keepalive = 5

# Logging
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Request line size
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Buffering
forwarded_allow_ips = '*'
proxy_allow_ips = '*'

# Security
secure_scheme_headers = {
    'X-FORWARDED_PROTOCOL': 'ssl',
    'X-FORWARDED_PROTO': 'ssl',
    'X-FORWARDED_SSL': 'on',
}

# WSGI app
app = None  # Will be set when starting gunicorn

print(f"✅ Gunicorn configured with:")
print(f"   - Bind: {bind}")
print(f"   - Workers: {workers}")
print(f"   - Timeout: {timeout}s ({timeout // 60} minutes)")
print(f"   - Worker class: {worker_class}")
print(f"   - Keep-alive: {keepalive}s")
