from django.contrib import admin
from .models import Video, HLSPlaylist, HLSSegment


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(HLSPlaylist)
class HLSPlaylistAdmin(admin.ModelAdmin):
    list_display = ('video', 'status', 'progress', 'estimated_size_mb', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('video__title',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(HLSSegment)
class HLSSegmentAdmin(admin.ModelAdmin):
    list_display = ('hls_playlist', 'rendition', 'segment_number', 'file_size_bytes')
    list_filter = ('rendition',)
    search_fields = ('hls_playlist__video__title',)
