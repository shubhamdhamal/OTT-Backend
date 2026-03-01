# ─────────────────────────────────────────────
#  OTT Backend — Production Dockerfile
#  Base: python:3.11-slim  |  Server: Gunicorn
# ─────────────────────────────────────────────

# ── Stage 1: build deps (keeps final image small) ──────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build-time system libs needed by some Python packages (psycopg2, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ─────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=ott_backend.settings \
    # HLS temp dir — must match docker-compose volume
    HLS_OUTPUT_DIR=/tmp/hls_videos

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \          
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create all required runtime directories
RUN mkdir -p /tmp/hls_videos \
             /app/media/uploads \
             /app/staticfiles \
             /var/log/ott && \
    # Non-root user for security
    groupadd -r django && useradd -r -g django django && \
    chown -R django:django /app /tmp/hls_videos /var/log/ott

USER django

# Collect static files at build time (needs a placeholder SECRET_KEY)
RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput --clear 2>/dev/null || true

EXPOSE 8000

# Healthcheck — hits the DRF API root
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/ || exit 1

# Entrypoint: migrate then start Gunicorn (config in gunicorn_config.py)
CMD ["sh", "-c", \
     "python manage.py migrate --noinput && \
      gunicorn ott_backend.wsgi:application -c gunicorn_config.py"]
