"""
HLS Streaming Service - Video Encoding with Adaptive Bitrate
Optimized for cost-effectiveness with 480p and 720p renditions
H.265 primary codec with H.264 fallback
Target file size: 700-850 MB
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import tempfile
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VideoRendition:
    """Represents a video quality rendition"""
    name: str
    resolution: str  # "480x270" or "1280x720"
    bitrate: str     # "800k" or "1400k"
    codec_primary: str    # "hevc" (H.265)
    codec_fallback: str   # "h264" (H.264)


class HLSEncodingConfig:
    """Configuration for HLS encoding"""
    
    # Target renditions as per client specs
    RENDITIONS = [
        VideoRendition(
            name="480p",
            resolution="854x480",
            bitrate="800k",
            codec_primary="hevc",
            codec_fallback="h264"
        ),
        VideoRendition(
            name="720p",
            resolution="1280x720",
            bitrate="1400k",
            codec_primary="hevc",
            codec_fallback="h264"
        ),
    ]
    
    # Segment configuration
    SEGMENT_DURATION = 6  # seconds per segment
    SEGMENT_COUNT = 0     # 0 = unlimited (VOD: include ALL segments in playlist)
    
    # Encoding settings
    CRF_HEVC = 28         # Quality (lower = better, 28 = good quality at lower bitrate)
    CRF_H264 = 28
    PRESET = "fast"       # Encoding speed: ultrafast, fast, medium, slow
    
    # Audio settings
    AUDIO_BITRATE = "128k"
    AUDIO_CODEC = "aac"
    AUDIO_SAMPLE_RATE = 44100


class HLSStreamingService:
    """Service for encoding videos to HLS format"""
    
    def __init__(self, output_dir: str = "/tmp/hls_output"):
        """Initialize HLS streaming service"""
        self.output_dir = output_dir
        self.config = HLSEncodingConfig()
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure output directory exists"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info("✅ FFmpeg is installed and available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ FFmpeg is not installed. Install it to enable HLS encoding.")
            return False
    
    def _get_video_duration(self, input_file: str) -> float:
        """Get video duration in seconds"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1:nokey=1",
                    input_file
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return 0
    
    def _get_video_bitrate(self, input_file: str) -> int:
        """Get video bitrate in kbps"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=bit_rate",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    input_file
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return int(result.stdout.strip()) // 1000  # Convert to kbps
        except Exception as e:
            logger.warning(f"Could not determine input bitrate: {e}")
            return 2500  # Default assumption
    
    def _estimate_encoded_size(
        self,
        duration_seconds: float,
        target_bitrate_kbps: int,
        include_audio: bool = True
    ) -> int:
        """Estimate encoded file size in MB"""
        # Video size
        video_size_mb = (duration_seconds * target_bitrate_kbps) / 8 / 1024
        
        # Audio size (128 kbps AAC)
        audio_size_mb = 0
        if include_audio:
            audio_size_mb = (duration_seconds * 128) / 8 / 1024
        
        total_size_mb = video_size_mb + audio_size_mb
        return total_size_mb
    
    def _encode_rendition_hevc(
        self,
        input_file: str,
        output_dir: str,
        rendition: VideoRendition
    ) -> bool:
        """Encode video to H.265 (HEVC) format"""
        logger.info(f"🎬 Encoding {rendition.name} with H.265 (HEVC)...")
        
        output_path = os.path.join(output_dir, rendition.name)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        playlist_file = os.path.join(output_path, "index.m3u8")
        segment_pattern = os.path.join(output_path, "segment_%03d.ts")
        
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-vf", f"scale={rendition.resolution}{':force_original_aspect_ratio=decrease' if ':' in rendition.resolution else ''}",
            "-c:v", "libx265",
            "-b:v", rendition.bitrate,
            "-tag:v", "hvc1",  # Compatible tag for H.265
            "-crf", str(self.config.CRF_HEVC),
            "-preset", self.config.PRESET,
            "-c:a", self.config.AUDIO_CODEC,
            "-b:a", self.config.AUDIO_BITRATE,
            "-ar", str(self.config.AUDIO_SAMPLE_RATE),
            "-ac", "2",               # Force stereo — Dolby Atmos/5.1/7.1 sources crash Flutter ExoPlayer in HLS TS
            "-af", "aresample=async=1", # Fix audio sync for multi-channel / variable-frame sources
            "-hls_time", str(self.config.SEGMENT_DURATION),
            "-hls_list_size", "0",        # 0 = keep ALL segments (required for VOD)
            "-hls_flags", "independent_segments",  # Each segment is independently decodable
            "-hls_segment_type", "mpegts",
            "-hls_segment_filename", segment_pattern,
            "-f", "hls",
            playlist_file,
            "-y"  # Overwrite output file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully encoded {rendition.name} (H.265)")
                return True
            else:
                logger.error(f"❌ Error encoding {rendition.name}: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Encoding timeout for {rendition.name}")
            return False
        except Exception as e:
            logger.error(f"❌ Exception during encoding {rendition.name}: {e}")
            return False
    
    def _encode_rendition_h264(
        self,
        input_file: str,
        output_dir: str,
        rendition: VideoRendition
    ) -> bool:
        """Encode video to H.264 format (fallback)"""
        logger.info(f"🎬 Encoding {rendition.name} with H.264 (fallback)...")
        
        output_path = os.path.join(output_dir, f"{rendition.name}_h264")
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        playlist_file = os.path.join(output_path, "index.m3u8")
        segment_pattern = os.path.join(output_path, "segment_%03d.ts")
        
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-vf", f"scale={rendition.resolution}",
            "-c:v", "libx264",
            "-b:v", rendition.bitrate,
            "-crf", str(self.config.CRF_H264),
            "-preset", self.config.PRESET,
            "-c:a", self.config.AUDIO_CODEC,
            "-b:a", self.config.AUDIO_BITRATE,
            "-ar", str(self.config.AUDIO_SAMPLE_RATE),
            "-ac", "2",               # Force stereo — Dolby Atmos/5.1/7.1 sources crash Flutter ExoPlayer in HLS TS
            "-af", "aresample=async=1", # Fix audio sync for multi-channel / variable-frame sources
            "-hls_time", str(self.config.SEGMENT_DURATION),
            "-hls_list_size", "0",        # 0 = keep ALL segments (required for VOD)
            "-hls_flags", "independent_segments",  # Each segment is independently decodable
            "-hls_segment_type", "mpegts",
            "-hls_segment_filename", segment_pattern,
            "-f", "hls",
            playlist_file,
            "-y"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully encoded {rendition.name} (H.264 fallback)")
                return True
            else:
                logger.error(f"❌ Error encoding {rendition.name} (H.264): {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Exception during H.264 encoding {rendition.name}: {e}")
            return False
    
    def _create_master_playlist(self, output_dir: str, use_h265: bool = True) -> bool:
        """Create master HLS playlist with codec variants"""
        logger.info("📝 Creating master playlist...")
        
        master_playlist_path = os.path.join(output_dir, "master.m3u8")
        
        playlist_content = "#EXTM3U\n"
        playlist_content += "#EXT-X-VERSION:3\n"
        playlist_content += "#EXT-X-INDEPENDENT-SEGMENTS\n\n"
        
        # H.265 variants (primary)
        if use_h265:
            playlist_content += "# H.265 (HEVC) - Primary variants\n"
            for rendition in self.config.RENDITIONS:
                playlist_content += (
                    f"#EXT-X-STREAM-INF:"
                    f"BANDWIDTH={int(rendition.bitrate[:-1]) * 1000},"
                    f"RESOLUTION={rendition.resolution},"
                    f"CODECS=\"hev1.1.6.L120.90,mp4a.40.2\"\n"  # Include audio codec so players init audio
                    f"{rendition.name}/index.m3u8\n\n"
                )
        
        # H.264 fallback variants
        playlist_content += "# H.264 - Fallback variants for compatibility\n"
        for rendition in self.config.RENDITIONS:
            playlist_content += (
                f"#EXT-X-STREAM-INF:"
                f"BANDWIDTH={int(rendition.bitrate[:-1]) * 1000},"
                f"RESOLUTION={rendition.resolution},"
                f"CODECS=\"avc1.42e01e,mp4a.40.2\"\n"
                f"{rendition.name}_h264/index.m3u8\n\n"
            )
        
        try:
            with open(master_playlist_path, "w") as f:
                f.write(playlist_content)
            logger.info(f"✅ Master playlist created: {master_playlist_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating master playlist: {e}")
            return False
    
    def encode_to_hls(self, input_file: str, video_id: str = None) -> Dict:
        """
        Encode video to HLS format with adaptive bitrate streaming
        
        Args:
            input_file: Path to input video file
            video_id: Optional video ID for naming output directories
        
        Returns:
            Dictionary with encoding results and metadata
        """
        if not os.path.exists(input_file):
            logger.error(f"❌ Input file not found: {input_file}")
            return {"success": False, "error": "Input file not found"}
        
        if not self._check_ffmpeg():
            return {"success": False, "error": "FFmpeg not installed"}
        
        # Create output directory
        video_name = video_id or Path(input_file).stem
        video_output_dir = os.path.join(self.output_dir, video_name)
        Path(video_output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🎥 Starting HLS encoding for: {video_name}")
        logger.info(f"📂 Output directory: {video_output_dir}")
        
        # Get video metadata
        duration = self._get_video_duration(input_file)
        input_bitrate = self._get_video_bitrate(input_file)
        
        logger.info(f"📊 Video duration: {duration:.2f}s ({duration/60:.2f} minutes)")
        logger.info(f"📊 Input bitrate: {input_bitrate} kbps")
        
        # Estimate output sizes
        sizes = {
            rendition.name: self._estimate_encoded_size(duration, int(rendition.bitrate[:-1]))
            for rendition in self.config.RENDITIONS
        }
        total_size = sum(sizes.values())
        
        logger.info(f"📊 Estimated output sizes:")
        for name, size in sizes.items():
            logger.info(f"   {name}: {size:.2f} MB")
        logger.info(f"   Total: {total_size:.2f} MB")
        
        if total_size > 900:
            logger.warning(
                f"⚠️  Estimated size ({total_size:.2f} MB) exceeds target range (700-850 MB). "
                "Consider reducing bitrates or video duration."
            )
        
        # Encode renditions
        encoding_results = {}
        hevc_success_count = 0
        
        for rendition in self.config.RENDITIONS:
            # Encode with H.265
            hevc_success = self._encode_rendition_hevc(
                input_file,
                video_output_dir,
                rendition
            )
            encoding_results[rendition.name] = {
                "hevc": hevc_success,
                "h264": False  # Will be set below
            }
            
            if hevc_success:
                hevc_success_count += 1
                # If H.265 succeeded, also encode H.264 fallback
                h264_success = self._encode_rendition_h264(
                    input_file,
                    video_output_dir,
                    rendition
                )
                encoding_results[rendition.name]["h264"] = h264_success
        
        # Create master playlist
        use_hevc = hevc_success_count > 0
        master_success = self._create_master_playlist(
            video_output_dir,
            use_h265=use_hevc
        )
        
        success = hevc_success_count > 0 and master_success
        
        return {
            "success": success,
            "video_id": video_name,
            "output_dir": video_output_dir,
            "master_playlist": os.path.join(video_output_dir, "master.m3u8"),
            "duration_seconds": duration,
            "duration_minutes": duration / 60,
            "input_bitrate_kbps": input_bitrate,
            "estimated_total_size_mb": total_size,
            "renditions": encoding_results,
            "metadata": {
                "hevc_codec_available": True,
                "h264_codec_available": True,
                "segment_duration": self.config.SEGMENT_DURATION,
                "segment_count": self.config.SEGMENT_COUNT,
            }
        }
    
    def get_playlist_url(self, video_id: str, cdn_base_url: str) -> str:
        """Get the CDN URL for the master HLS playlist"""
        return f"{cdn_base_url}/{video_id}/master.m3u8"
    
    def cleanup(self, video_id: str = None):
        """Clean up encoding output"""
        if video_id:
            video_dir = os.path.join(self.output_dir, video_id)
            if os.path.exists(video_dir):
                shutil.rmtree(video_dir)
                logger.info(f"✅ Cleaned up: {video_dir}")
        else:
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
                logger.info(f"✅ Cleaned up: {self.output_dir}")


# Example usage
if __name__ == "__main__":
    # Initialize service
    service = HLSStreamingService(output_dir="/tmp/hls_videos")
    
    # Example: Encode a video
    # result = service.encode_to_hls(
    #     input_file="/path/to/video.mp4",
    #     video_id="video_123"
    # )
    # print(json.dumps(result, indent=2))
