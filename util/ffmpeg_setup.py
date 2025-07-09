#!/usr/bin/env python3
"""
FFprobe static binary downloader for environments without package manager access
Works with Heroku, Koyeb, Railway, and other Buildpack platforms
"""

import os
import asyncio
import aiohttp
import logging
import stat
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

class FFprobeInstaller:
    def __init__(self):
        self.binary_dir = Path("bin")
        self.ffprobe_path = self.binary_dir / "ffprobe"
        
        # Static binary URLs for different architectures
        self.binary_urls = {
            "linux_x86_64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b6.0/ffprobe-linux-x64",
            "linux_arm64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b6.0/ffprobe-linux-arm64", 
            "darwin_x86_64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b6.0/ffprobe-darwin-x64",
            "darwin_arm64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b6.0/ffprobe-darwin-arm64"
        }
    
    def get_platform_key(self):
        """Determine the platform and architecture"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Normalize architecture names
        if machine in ["x86_64", "amd64"]:
            arch = "x86_64"
        elif machine in ["arm64", "aarch64"]:
            arch = "arm64"
        else:
            arch = "x86_64"  # Default fallback
        
        return f"{system}_{arch}"
    
    async def download_ffprobe(self):
        """Download static ffprobe binary"""
        platform_key = self.get_platform_key()
        
        if platform_key not in self.binary_urls:
            logger.error(f"Unsupported platform: {platform_key}")
            return False
        
        url = self.binary_urls[platform_key]
        
        try:
            # Create bin directory
            self.binary_dir.mkdir(exist_ok=True)
            
            logger.info(f"Downloading ffprobe for {platform_key}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download ffprobe: HTTP {response.status}")
                        return False
                    
                    # Download binary
                    with open(self.ffprobe_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            # Make executable
            os.chmod(self.ffprobe_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            
            logger.info(f"Successfully downloaded ffprobe to {self.ffprobe_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading ffprobe: {e}")
            return False
    
    def is_ffprobe_available(self):
        """Check if ffprobe is available (system or downloaded)"""
        # Check system ffprobe first
        if self._check_system_ffprobe():
            return "system"
        
        # Check downloaded binary
        if self.ffprobe_path.exists() and os.access(self.ffprobe_path, os.X_OK):
            return "downloaded"
        
        return None
    
    def _check_system_ffprobe(self):
        """Check if system ffprobe is available"""
        try:
            import subprocess
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_ffprobe_command(self):
        """Get the appropriate ffprobe command"""
        availability = self.is_ffprobe_available()
        
        if availability == "system":
            return "ffprobe"
        elif availability == "downloaded":
            return str(self.ffprobe_path.absolute())
        else:
            return None
    
    async def ensure_ffprobe(self):
        """Ensure ffprobe is available, download if needed"""
        availability = self.is_ffprobe_available()
        
        if availability:
            logger.info(f"ffprobe is available ({availability})")
            return True
        
        logger.info("ffprobe not found, attempting to download...")
        success = await self.download_ffprobe()
        
        if success:
            # Verify the download worked
            if self.is_ffprobe_available():
                logger.info("ffprobe successfully installed!")
                return True
            else:
                logger.error("ffprobe download verification failed")
                return False
        else:
            logger.error("Failed to download ffprobe")
            return False

# Global instance
ffprobe_installer = FFprobeInstaller()

async def setup_ffprobe():
    """Setup ffprobe for the application"""
    return await ffprobe_installer.ensure_ffprobe()

def get_ffprobe_command():
    """Get the ffprobe command path"""
    return ffprobe_installer.get_ffprobe_command()