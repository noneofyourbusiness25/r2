# Media Information Feature

## Overview

This feature adds media information extraction capability to your Telegram bot without requiring database modification or re-adding existing files. Users can now view detailed information about media files including duration, audio tracks, subtitles, format, and more.

## How It Works

### On-Demand Processing
- Media information is extracted only when users click the "📋 Media Info" button
- No pre-processing of existing database files required
- Uses ffprobe (part of ffmpeg) for accurate media analysis

### Smart Optimization
- Downloads only the first 2MB of files for analysis (sufficient for media headers)
- Caches results temporarily (5 minutes) to avoid repeated processing
- Auto-detects non-media files and provides basic info without downloading

### Temporary Display
- Media info is shown for 2 minutes then auto-deleted to keep chats clean
- Users can manually close the info with the "❌ Close Info" button
- Processing messages are shown to users during extraction

## Features

### Information Displayed
- **Basic Info**: File format, duration, size, bitrate
- **Video Details**: Codec, resolution (width x height)
- **Audio Tracks**: Multiple audio tracks with language, codec, channels
- **Subtitles**: Available subtitle tracks with languages
- **Smart Formatting**: Human-readable durations and file sizes

### Example Output
```
📋 Media Information

📁 File: Movie.2023.1080p.mkv
📦 Format: MATROSKA,WEBM
⏱ Duration: 2h 15m 30s
📏 Size: 1.98 GB
🔗 Bitrate: 8500 kbps

🎬 Video: h264 (1920x1080)
🔊 Audio Tracks: 3
   • English Audio (eng) - ac3 - 6ch
   • Hindi Dub (hin) - aac - 2ch
   • Commentary (eng) - mp3 - 2ch

💬 Subtitles: 5
   • English (eng)
   • Spanish (spa)
   • French (fra)
   • ... and 2 more
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

## Usage

### For Users
1. Request any file from the bot as usual
2. When the file is sent, look for the "📋 Media Info" button
3. Click the button to see detailed media information
4. Info will auto-delete after 2 minutes or can be closed manually

### For Admins
- No configuration required
- Feature works automatically once deployed
- Monitor logs for any ffprobe errors if needed

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

- This implementation prioritizes minimal server load over comprehensive analysis
- For production use with high traffic, consider implementing rate limiting
- The feature is designed to work with your existing database without modifications
- All processing is done on-demand to maintain server performance