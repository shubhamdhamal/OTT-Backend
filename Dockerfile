# OTT Backend Docker Configuration
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY HLS_REQUIREMENTS.txt .
RUN pip install --upgrade pip && \
    pip install -r HLS_REQUIREMENTS.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /var/media/hls_videos /var/log

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && gunicorn ott_backend.wsgi:application --bind 0.0.0.0:8000"]
