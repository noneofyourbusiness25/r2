# Media Information Feature

## Overview

This feature adds media information extraction capability to your Telegram bot without requiring database modification or re-adding existing files. Users can now view detailed information about media files including duration, audio tracks, subtitles, format, and more.

## How It Works

### On-Demand Processing
- Media information is extracted only when users click the "📋 Media Info" button
- No pre-processing of existing database files required
- Uses ffprobe (part of ffmpeg) for detailed analysis when available
- **Automatic fallback mode** when ffprobe is not installed

### Smart Optimization
- Downloads only the first 3MB of files for analysis (sufficient for media headers)
- Caches results temporarily (5 minutes) to avoid repeated processing
- **Automatic fallback** when ffprobe is not available
- Intelligent file analysis using filename patterns and database info

### Temporary Display
- Media info is shown for 2 minutes then auto-deleted to keep chats clean
- Users can manually close the info with the "❌ Close Info" button
- Processing messages are shown to users during extraction

## Features

### Two Modes of Operation

#### **Full Mode (with ffprobe installed)**
- **Complete Analysis**: File format, duration, size, bitrate
- **Video Details**: Codec, resolution, framerate
- **Audio Tracks**: Multiple tracks with language, codec, channels, sample rate
- **Subtitles**: Available subtitle tracks with languages and codecs
- **Chapters**: Movie/episode chapters with timestamps
- **Smart Formatting**: Human-readable durations and file sizes

#### **Fallback Mode (no ffprobe needed)**
- **Basic Info**: File format (from extension/mime), size
- **Intelligent Guessing**: Resolution from filename (1080p, 720p, etc.)
- **Language Detection**: Audio languages from filename patterns
- **No Installation Required**: Works immediately without server changes

### Example Output

#### **Full Mode (with ffprobe)**
```
📋 Media Information

📁 File: The.Avengers.2012.1080p.mkv
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
   • Natasha's Interrogation - 11m 49s
   • ... and 17 more
```

#### **Fallback Mode (no ffprobe)**
```
📋 Media Information

📁 File: The.Avengers.2012.720p.Hindi.English.mkv
� Format: MATROSKA/MKV
⏱ Duration: Not Available (Install ffmpeg for duration)
📏 Size: 1.40 GB
🔗 Bitrate: Not Available (Install ffmpeg for bitrate)

💡 Limited info - Install ffmpeg for detailed analysis

🎬 Video: Unknown (1280x720)
🔊 Audio Tracks: 2
   • Hindi (hin) - Unknown
   • English (eng) - Unknown
```

## Files Modified

### New Files
- `util/media_info.py` - Core media information extraction logic

### Modified Files
- `plugins/commands.py` - Added media info button and callback handlers
- Added import for media extractor
- Added callback handlers for media info button clicks

## Server Load Considerations

### Minimal Resource Usage
- Only processes files when explicitly requested by users
- Downloads minimal data (2MB chunks) for analysis
- Automatic cleanup of temporary files
- Short-term caching reduces repeated processing

### Smart Filtering
- Non-media files are detected by extension and handled quickly
- Processing stops immediately for corrupted or unsupported files
- Background auto-deletion prevents memory buildup

## Installation & Usage

### Server Setup

#### **🎯 Automatic Setup (Recommended)**
The bot now **automatically downloads** ffprobe on startup!

- **Works on Koyeb, Heroku, Railway** and other Buildpack platforms
- **No manual installation required**
- **Downloads appropriate binary** for your server architecture
- **Falls back gracefully** if download fails

#### **🛠️ Manual Installation (Optional)**
If you have system access and want to install FFmpeg manually:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL/Rocky Linux
sudo yum install epel-release
sudo yum install ffmpeg

# Verify installation
ffprobe -version
```

#### **⚡ Immediate Deployment**
Just deploy and run - no server changes needed!

### For Users
1. Request any file from the bot as usual
2. When the file is sent, look for the "📋 Media Info" button
3. Click the button to see media information
4. Info will auto-delete after 2 minutes or can be closed manually

### For Admins
- **No configuration required** - works automatically
- **Automatic fallback** if ffprobe is not available
- Monitor logs to see which mode is being used

## Technical Details

### Dependencies
- `ffmpeg` and `ffmpeg-python` (already in requirements.txt)
- Uses ffprobe for media analysis
- Temporary file handling with automatic cleanup

### Error Handling
- Graceful fallback for unsupported formats
- User-friendly error messages
- Automatic cleanup on failures

### Security
- No permanent file storage on server
- Temporary files are immediately deleted after analysis
- Limited download size prevents abuse

## Performance Tips

### For Server Owners
- Ensure ffmpeg is properly installed
- Monitor disk space in /tmp directory
- Consider rate limiting if needed for heavy usage

### File Type Support
- **Video**: MP4, MKV, AVI, MOV, WMV, FLV, WebM, M4V, 3GP
- **Audio**: MP3, FLAC, AAC, OGG, WMA, WAV, M4A, Opus
- **Other**: Basic info only (format, extension)

## Troubleshooting

### Common Issues
1. **"Could not extract media information"**
   - File might be corrupted
   - Unsupported format
   - Network issues during download

2. **Slow processing**
   - Large files take longer to download headers
   - Server load might be high
   - Network connectivity issues

3. **ffprobe errors in logs**
   - Ensure ffmpeg is properly installed
   - Check file format compatibility

## Future Enhancements

Potential improvements that could be added:
- Thumbnail extraction for videos
- Detailed codec information
- Audio/video quality analysis
- File integrity checking
- Custom format templates

## Notes

- **Buildpack Compatible**: Now works on Koyeb, Heroku, Railway without system access
- **Automatic Setup**: Downloads ffprobe binary on first startup
- **Graceful Fallback**: Works even if binary download fails
- **No Database Changes**: Works with your existing files
- **Minimal Server Load**: Only processes files when requested
- **Production Ready**: Handles high traffic with caching and optimization

## Koyeb/Buildpack Deployment

This solution specifically addresses the **ffprobe not found** issue on Buildpack platforms:

1. **Automatic Binary Download**: Downloads static ffprobe binary on startup
2. **Architecture Detection**: Automatically detects x86_64/ARM64 platforms
3. **Persistent Storage**: Binary stored in `/bin` directory (excluded from git)
4. **Fallback Safety**: Continues working even if download fails
5. **Zero Configuration**: Just deploy and it works

### Startup Logs
When your bot starts, you'll see:
```
Setting up media analysis tools...
Downloading ffprobe for linux_x86_64...
Successfully downloaded ffprobe to bin/ffprobe
✅ Media analysis ready (ffprobe available)
```

Or if download fails:
```
Setting up media analysis tools...
⚠️ Media analysis in fallback mode (ffprobe unavailable)
```