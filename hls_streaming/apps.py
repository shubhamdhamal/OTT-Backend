from django.apps import AppConfig


class HlsStreamingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hls_streaming'
    verbose_name = 'HLS Video Streaming'
