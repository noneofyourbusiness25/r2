# 🚀 Quick Setup Guide - Media Info Feature

## 📁 Files Created/Updated

### ✅ New Files Created:
1. **`util/ffmpeg_setup.py`** - Automatic ffprobe downloader
2. **`util/media_info_complete.py`** - Enhanced media info extractor  
3. **`commands_media_handlers.py`** - Media info button handlers
4. **`bot_complete.py`** - Complete bot.py with ffprobe setup
5. **`DEPLOY_MEDIA_INFO.md`** - Complete deployment documentation
6. **`requirements_media.txt`** - Additional dependencies

### ✅ Files to Update:
1. **`bot.py`** - Add ffprobe setup (see bot_complete.py for reference)
2. **`plugins/commands.py`** - Add handlers from commands_media_handlers.py
3. **`requirements.txt`** - Add aiohttp>=3.8.0, aiofiles>=0.8.0
4. **`.gitignore`** - Add bin/ and *.tmp exclusions
5. **Your file sending code** - Add media info button

## 🔧 Essential Steps:

### Step 1: Copy Files
```bash
# Copy the new files to your project:
cp util/ffmpeg_setup.py your-project/util/
cp util/media_info_complete.py your-project/util/
```

### Step 2: Update Bot Startup
Add to your `bot.py` after `await Media.ensure_indexes()`:
```python
from util.ffmpeg_setup import setup_ffprobe

# Setup ffprobe for media analysis
print("Setting up media analysis tools...")
ffprobe_ready = await setup_ffprobe()
if ffprobe_ready:
    print("✅ Media analysis ready (ffprobe available)")
else:
    print("⚠️ Media analysis in fallback mode (ffprobe unavailable)")
```

### Step 3: Add Media Info Button
In your file sending code, add:
```python
[InlineKeyboardButton('📋 Media Info', callback_data=f'mediainfo#{file_id}')]
```

### Step 4: Add Callback Handlers
Copy the handlers from `commands_media_handlers.py` to your `plugins/commands.py`

### Step 5: Update Dependencies
Add to `requirements.txt`:
```
aiohttp>=3.8.0
aiofiles>=0.8.0
```

### Step 6: Deploy
```bash
git add .
git commit -m "Add automatic media info feature with Buildpack ffprobe support"
git push
```

## 🎯 Expected Results:

**✅ Success:** Bot automatically downloads ffprobe and shows detailed media info
**⚠️ Fallback:** If download fails, shows basic info with helpful hints

## 📋 What Users See:

### With ffprobe (Full Features):
```
📋 Media Information

📁 File: Movie.2024.1080p.mkv
📦 Format: MATROSKA,WEBM
⏱ Duration: 2h 15m 30s
📏 Size: 2.1 GB
🔗 Bitrate: 2145 kbps

🎬 Video: h264 (1920x1080)
🔊 Audio Tracks: 2
   • English (eng) - aac - 6ch
   • Hindi (hin) - aac - 2ch
💬 Subtitles: 1
   • English (eng) - subrip
```

### Fallback Mode (Basic Info):
```
📋 Media Information

📁 File: Movie.2024.1080p.mkv
📦 Format: MATROSKA/MKV
⏱ Duration: Not Available (Install ffmpeg for duration)
📏 Size: 2.1 GB

💡 Limited info - Install ffmpeg for detailed analysis
```

## 🏆 This Solves:
- ✅ **ffprobe not found** errors on Koyeb/Heroku
- ✅ **Media info extraction** for all users
- ✅ **Zero configuration** deployment
- ✅ **Cross-platform** compatibility

**Ready to deploy! 🚀**