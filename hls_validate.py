"""
HLS Backend System Validator
Checks if all dependencies and configurations are properly set up
"""

import os
import sys
import subprocess
import json

class HLSValidator:
    """Validates HLS backend setup"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []
    
    def check_python_version(self):
        """Check Python version compatibility"""
        version_info = sys.version_info
        if version_info.major == 3 and version_info.minor >= 8:
            self.success.append(f"✅ Python {version_info.major}.{version_info.minor} - OK")
        else:
            self.errors.append(f"❌ Python 3.8+ required (found {version_info.major}.{version_info.minor})")
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=True)
            self.success.append("✅ FFmpeg - Installed")
        except:
            self.errors.append("❌ FFmpeg - NOT installed (required for video encoding)")
    
    def check_redis(self):
        """Check if Redis is running"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            self.success.append("✅ Redis - Running")
        except:
            self.warnings.append("⚠️  Redis - Not available (async tasks will fail)")
    
    def check_django(self):
        """Check if Django is installed"""
        try:
            import django
            self.success.append(f"✅ Django {django.get_version()} - Installed")
        except:
            self.errors.append("❌ Django - NOT installed")
    
    def check_dependencies(self):
        """Check required Python packages"""
        required = [
            'rest_framework',
            'celery',
            'PIL',  # Pillow
            'redis',
        ]
        
        for package in required:
            try:
                __import__(package)
                self.success.append(f"✅ {package} - Installed")
            except ImportError:
                self.errors.append(f"❌ {package} - NOT installed")
    
    def check_directories(self):
        """Check if required directories exist"""
        directories = {
            '/var/media/hls_videos': 'HLS output directory',
            '/var/log': 'Log directory',
        }
        
        for directory, description in directories.items():
            if os.path.exists(directory) and os.path.isdir(directory):
                self.success.append(f"✅ {directory} ({description}) - OK")
            else:
                self.warnings.append(f"⚠️  {directory} ({description}) - Create before encoding")
    
    def check_django_settings(self):
        """Check if Django settings are configured"""
        try:
            from django.conf import settings
            
            # Check HLS_OUTPUT_DIR
            if hasattr(settings, 'HLS_OUTPUT_DIR'):
                self.success.append(f"✅ Django HLS_OUTPUT_DIR - Configured: {settings.HLS_OUTPUT_DIR}")
            else:
                self.warnings.append("⚠️  Django HLS_OUTPUT_DIR - Not configured in settings")
            
            # Check Celery
            if hasattr(settings, 'CELERY_BROKER_URL'):
                self.success.append("✅ Django Celery - Configured")
            else:
                self.warnings.append("⚠️  Django Celery - Not configured (async encoding will fail)")
        
        except Exception as e:
            self.errors.append(f"❌ Django Settings - Error: {str(e)}")
    
    def run_all_checks(self):
        """Run all validation checks"""
        print("=" * 60)
        print("HLS Backend System Validator")
        print("=" * 60)
        print()
        
        self.check_python_version()
        self.check_ffmpeg()
        self.check_redis()
        self.check_django()
        self.check_dependencies()
        self.check_directories()
        self.check_django_settings()
        
        print("✅ SUCCESS:")
        for item in self.success:
            print(f"  {item}")
        
        if self.warnings:
            print()
            print("⚠️  WARNINGS:")
            for item in self.warnings:
                print(f"  {item}")
        
        if self.errors:
            print()
            print("❌ ERRORS:")
            for item in self.errors:
                print(f"  {item}")
        
        print()
        print("=" * 60)
        
        if self.errors:
            print("Status: ❌ SETUP INCOMPLETE - Fix errors before proceeding")
            return False
        elif self.warnings:
            print("Status: ⚠️  WARNING - Some optional components missing")
            return True
        else:
            print("Status: ✅ ALL CHECKS PASSED - Ready for deployment!")
            return True


if __name__ == '__main__':
    validator = HLSValidator()
    success = validator.run_all_checks()
    sys.exit(0 if success else 1)
