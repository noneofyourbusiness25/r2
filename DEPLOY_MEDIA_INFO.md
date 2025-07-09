# 🚀 Complete Media Info Feature Deployment Guide

## 📋 Overview

This guide provides a complete solution for adding media information extraction to your Telegram bot that works on **Koyeb, Heroku, Railway** and other Buildpack platforms where `apt-get` is not available.

### ✨ What This Adds:
- **📋 Media Info button** on all sent files
- **🔄 Automatic ffprobe download** on Buildpack platforms
- **📊 Detailed media analysis** (duration, codecs, audio tracks, subtitles)
- **⚡ Intelligent fallback** when ffprobe unavailable
- **🎯 Zero configuration** required

## 📁 Files to Create/Update

### 1. **`util/ffmpeg_setup.py`** (NEW - Critical)
This automatically downloads ffprobe for Buildpack platforms:

```python
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
```

### 2. **Update `bot.py`**
Add ffprobe setup to your bot startup:

**Add this import:**
```python
from util.ffmpeg_setup import setup_ffprobe
```

**Add this to your startup function (after `await Media.ensure_indexes()`):**
```python
# Setup ffprobe for media analysis
print("Setting up media analysis tools...")
ffprobe_ready = await setup_ffprobe()
if ffprobe_ready:
    print("✅ Media analysis ready (ffprobe available)")
else:
    print("⚠️ Media analysis in fallback mode (ffprobe unavailable)")
```

### 3. **Update Your File Sending Code**
Add the media info button to your file messages:

**In your existing file sending code, add this button:**
```python
[InlineKeyboardButton('📋 Media Info', callback_data=f'mediainfo#{file_id}')]
```

**Example:**
```python
reply_markup=InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
        InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
    ],
    [
        InlineKeyboardButton('📋 Media Info', callback_data=f'mediainfo#{file_id}')
    ]
])
```

### 4. **Add Media Info Handlers to `plugins/commands.py`**
Add these callback handlers:

```python
from util.media_info_complete import media_extractor

@Client.on_callback_query(filters.regex(r"^mediainfo#"))
async def media_info_callback(client, query):
    """Handle media info button callback"""
    try:
        _, file_id = query.data.split("#")
        
        # Get file details from database
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer("❌ File not found!", show_alert=True)
        
        files = files_[0]
        file_name = files.file_name
        
        # Show processing message
        processing_msg = await query.message.reply_text(
            "🔄 <b>Extracting media information...</b>\n\n"
            f"📁 Analyzing: <code>{file_name}</code>\n"
            "This may take a few seconds...",
            quote=True
        )
        
        # Extract media info
        media_info = await media_extractor.extract_media_info(client, file_id, file_name)
        
        if media_info:
            # Format the information message
            info_message = media_extractor.format_media_info_message(media_info, file_name)
            
            # Add close button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close Info", callback_data="close_mediainfo")]
            ])
            
            # Edit the processing message with media info
            await processing_msg.edit_text(
                text=info_message,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
            
            # Auto-delete after 2 minutes to keep chat clean
            asyncio.create_task(auto_delete_media_info(processing_msg, 120))
            
        else:
            await processing_msg.edit_text(
                "❌ <b>Could not extract media information</b>\n\n"
                f"📁 File: <code>{file_name}</code>\n"
                "• File format might not be supported\n"
                "• File might be corrupted\n"
                "• Download may have failed\n\n"
                "<i>Check bot logs for detailed error information.</i>"
            )
            
            # Auto-delete after 30 seconds
            asyncio.create_task(auto_delete_media_info(processing_msg, 30))
        
        await query.answer()
        
    except Exception as e:
        logger.error(f"Error in media info callback: {e}")
        await query.answer("❌ Error extracting media information", show_alert=True)

@Client.on_callback_query(filters.regex(r"^close_mediainfo"))
async def close_media_info(client, query):
    """Handle close media info button"""
    try:
        await query.message.delete()
        await query.answer("Media info closed")
    except Exception as e:
        logger.error(f"Error closing media info: {e}")
        await query.answer()

async def auto_delete_media_info(message, delay_seconds):
    """Auto delete media info message after specified delay"""
    try:
        await asyncio.sleep(delay_seconds)
        await message.delete()
    except Exception as e:
        logger.error(f"Error auto-deleting media info: {e}")
```

### 5. **Update `.gitignore`**
Add these lines to exclude downloaded binaries:

```
# Downloaded ffprobe binaries
bin/
*.tmp

# Media analysis temporary files
*.tmp.*
media_temp/
```

## 🚀 Deployment Steps

### **Step 1: Add Files**
1. Create `util/ffmpeg_setup.py` with the content above
2. Copy the complete `util/media_info_complete.py` content
3. Update your `bot.py` with ffprobe setup
4. Add media info handlers to `plugins/commands.py`
5. Add media info button to your file sending code
6. Update `.gitignore`

### **Step 2: Commit & Deploy**
```bash
git add .
git commit -m "Add automatic media info feature with Buildpack ffprobe support"
git push
```

### **Step 3: Deploy to Koyeb/Platform**
Deploy as you normally would. The bot will automatically:
1. **Detect platform** (linux_x86_64, etc.)
2. **Download ffprobe** binary on first startup
3. **Setup media analysis** capabilities
4. **Show status** in startup logs

## 📊 Expected Results

### **✅ Successful Setup**
```
Setting up media analysis tools...
Downloading ffprobe for linux_x86_64...
Successfully downloaded ffprobe to bin/ffprobe
✅ Media analysis ready (ffprobe available)
```

**Users will see:**
```
📋 Media Information

📁 File: The.Avengers.2012.720p.Hindi.English.mkv
📦 Format: MATROSKA,WEBM
⏱ Duration: 2h 23m 15s
📏 Size: 1.40 GB
🔗 Bitrate: 1372 kbps

🎬 Video: h264 (1280x720)
🔊 Audio Tracks: 2
   • Hindi Audio (hin) - aac - 6ch
   • English Audio (eng) - aac - 2ch

💬 Subtitles: 1
   • English (eng) - subrip

📖 Chapters: 20 (showing first 5)
   • Loki's Arrival - 0s
   • Tesseract Lost - 8m 2s
   • ... and 17 more
```

### **⚠️ Fallback Mode (if download fails)**
```
Setting up media analysis tools...
⚠️ Media analysis in fallback mode (ffprobe unavailable)
```

**Users will still see useful info:**
```
📋 Media Information

📁 File: The.Avengers.2012.720p.Hindi.English.mkv
📦 Format: MATROSKA/MKV
⏱ Duration: Not Available (Install ffmpeg for duration)
📏 Size: 1.40 GB
🔗 Bitrate: Not Available (Install ffmpeg for bitrate)

💡 Limited info - Install ffmpeg for detailed analysis

🎬 Video: Unknown (1280x720)
🔊 Audio Tracks: 2
   • Hindi (hin) - Unknown
   • English (eng) - Unknown
```

## 🔧 Troubleshooting

### **Issue: Download Fails**
- **Check logs** for specific error messages
- **Verify internet access** during bot startup
- **Platform detection** should show correct architecture

### **Issue: Button Not Appearing**
- **Verify** you added the button to file sending code
- **Check imports** in commands.py
- **Restart bot** after code changes

### **Issue: Analysis Fails**
- **Check logs** for detailed error messages
- **Large files** may take longer to process
- **Corrupted files** will show error message

## 🎯 Features

### **Automatic Setup**
- ✅ **Zero configuration** required
- ✅ **Cross-platform** detection (x86_64, ARM64)
- ✅ **Graceful fallback** if download fails
- ✅ **Works on Koyeb, Heroku, Railway**

### **Media Analysis**
- ✅ **File format** and container info
- ✅ **Duration** and file size
- ✅ **Video codec** and resolution
- ✅ **Multiple audio tracks** with languages
- ✅ **Subtitle tracks** with languages
- ✅ **Chapter information** for movies/shows
- ✅ **Bitrate** and technical details

### **User Experience**
- ✅ **Clean interface** with auto-delete
- ✅ **Fast processing** with caching
- ✅ **Error handling** with helpful messages
- ✅ **Mobile-friendly** formatting

## 🏆 Benefits

1. **Buildpack Compatible** - Works without system access
2. **Zero Configuration** - Just deploy and it works
3. **Intelligent Fallback** - Always provides some information
4. **Production Ready** - Handles high traffic efficiently
5. **User Friendly** - Clean, informative display

This solution completely resolves the `ffprobe not found` issue on Buildpack platforms while maintaining full functionality! 🎉