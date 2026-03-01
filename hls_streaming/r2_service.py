"""
Cloudflare R2 Storage Service
Handles uploading HLS segments and playlists to R2
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class R2StorageService:
    """Service for uploading HLS files to Cloudflare R2"""
    
    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str = "ott-videos",
        region: str = "auto",
        public_domain: str = None
    ):
        """
        Initialize R2 storage service
        
        Args:
            account_id: Cloudflare account ID
            access_key_id: R2 access key ID
            secret_access_key: R2 secret access key
            bucket_name: R2 bucket name
            region: R2 region (usually 'auto')
        """
        self.bucket_name = bucket_name
        self.account_id = account_id
        # Public CDN domain for serving files (no auth required)
        # Falls back to private endpoint if not set (will cause 403 errors!)
        self.public_domain = public_domain.rstrip('/') if public_domain else None
        
        # Initialize S3 client for R2
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
        
        logger.info(f"✅ R2 Storage Service initialized for bucket: {bucket_name}")
    
    def upload_file(
        self,
        local_file_path: str,
        r2_key: str,
        content_type: str = "application/octet-stream"
    ) -> Tuple[bool, str]:
        """
        Upload a single file to R2
        
        Args:
            local_file_path: Path to local file
            r2_key: S3 key (path) in R2 bucket
            content_type: MIME type of file
        
        Returns:
            Tuple of (success: bool, url_or_error: str)
        """
        try:
            if not os.path.exists(local_file_path):
                logger.error(f"❌ Local file not found: {local_file_path}")
                return False, f"File not found: {local_file_path}"
            
            file_size = os.path.getsize(local_file_path)
            logger.info(f"📤 Uploading {r2_key} ({file_size / 1024 / 1024:.2f} MB)...")
            
            with open(local_file_path, 'rb') as f:
                self.s3_client.upload_fileobj(
                    f,
                    self.bucket_name,
                    r2_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'public, max-age=31536000'  # 1 year for segments
                    }
                )
            
            # Construct public CDN URL (not the private API endpoint)
            if self.public_domain:
                url = f"{self.public_domain}/{r2_key}"
            else:
                # Fallback: private URL (will require auth - use public_domain in production!)
                url = f"https://{self.account_id}.r2.cloudflarestorage.com/{self.bucket_name}/{r2_key}"
                logger.warning(f"⚠️  No R2_PUBLIC_DOMAIN set! Using private URL which requires auth.")
            logger.info(f"✅ Uploaded: {url}")
            return True, url
        
        except ClientError as e:
            logger.error(f"❌ R2 upload error: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"❌ Unexpected error uploading {r2_key}: {e}")
            return False, str(e)
    
    def upload_directory(
        self,
        local_dir: str,
        r2_prefix: str = "",
        extensions: list = None
    ) -> Dict[str, list]:
        """
        Recursively upload directory contents to R2
        
        Args:
            local_dir: Local directory path
            r2_prefix: Prefix path in R2 (e.g., "videos/video_123")
            extensions: List of file extensions to upload (e.g., ['.m3u8', '.ts'])
        
        Returns:
            Dict with 'success' and 'failed' lists of URLs/errors
        """
        if extensions is None:
            extensions = ['.m3u8', '.ts', '.jpg', '.png']
        
        results = {
            'success': [],
            'failed': []
        }
        
        if not os.path.isdir(local_dir):
            logger.error(f"❌ Directory not found: {local_dir}")
            return results
        
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                # Check if file extension matches
                if not any(file.endswith(ext) for ext in extensions):
                    continue
                
                local_file_path = os.path.join(root, file)
                
                # Calculate R2 key (preserve directory structure)
                relative_path = os.path.relpath(local_file_path, local_dir)
                r2_key = f"{r2_prefix}/{relative_path}".strip('/').replace('\\', '/')
                
                # Determine content type
                if file.endswith('.m3u8'):
                    content_type = 'application/vnd.apple.mpegurl'
                elif file.endswith('.ts'):
                    content_type = 'video/MP2T'
                elif file.endswith('.jpg'):
                    content_type = 'image/jpeg'
                elif file.endswith('.png'):
                    content_type = 'image/png'
                else:
                    content_type = 'application/octet-stream'
                
                # Upload file
                success, url_or_error = self.upload_file(
                    local_file_path,
                    r2_key,
                    content_type
                )
                
                if success:
                    results['success'].append(url_or_error)
                    total_size += os.path.getsize(local_file_path)
                    file_count += 1
                else:
                    results['failed'].append({
                        'file': local_file_path,
                        'error': url_or_error
                    })
        
        logger.info(f"✅ Upload complete: {file_count} files, {total_size / 1024 / 1024:.2f} MB total")
        if results['failed']:
            logger.warning(f"⚠️  Failed uploads: {len(results['failed'])}")
        
        return results
    
    def get_master_playlist_url(self, video_id: str) -> str:
        """Get the public CDN URL for master playlist"""
        r2_key = f"videos/{video_id}/master.m3u8"
        if self.public_domain:
            return f"{self.public_domain}/{r2_key}"
        # Fallback: private URL (will fail without auth)
        logger.warning(f"⚠️  No R2_PUBLIC_DOMAIN set! Master playlist URL will require auth.")
        return f"https://{self.account_id}.r2.cloudflarestorage.com/{self.bucket_name}/{r2_key}"
    
    def delete_file(self, r2_key: str) -> bool:
        """Delete a file from R2"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=r2_key
            )
            logger.info(f"✅ Deleted from R2: {r2_key}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting {r2_key}: {e}")
            return False
    
    def delete_directory(self, r2_prefix: str) -> int:
        """Delete all files under a prefix in R2"""
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=r2_prefix
            )
            
            deleted_count = 0
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        self.s3_client.delete_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        deleted_count += 1
            
            logger.info(f"✅ Deleted {deleted_count} files from R2 under prefix: {r2_prefix}")
            return deleted_count
        except Exception as e:
            logger.error(f"❌ Error deleting directory {r2_prefix}: {e}")
            return 0


def get_r2_service_from_settings(settings) -> Optional[R2StorageService]:
    """Helper to initialize R2 service from Django settings"""
    try:
        # Check if R2 is configured
        if not hasattr(settings, 'R2_ACCOUNT_ID'):
            logger.warning("R2 not configured in settings")
            return None
        
        return R2StorageService(
            account_id=settings.R2_ACCOUNT_ID,
            access_key_id=settings.R2_ACCESS_KEY_ID,
            secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            bucket_name=getattr(settings, 'R2_BUCKET_NAME', 'ott-videos'),
            public_domain=getattr(settings, 'R2_PUBLIC_DOMAIN', None)
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize R2 service: {e}")
        return None
