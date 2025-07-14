# 📊 Media Info Feature

This bot now includes an optional **Media Info** feature that provides detailed information about video files without causing server overload.

## ✨ Features

- **On-Demand Analysis**: Media information is only processed when users click the "📊 Media Info" button
- **Comprehensive Details**: Shows video codec, resolution, audio info, subtitles, duration, bitrate, and more
- **Smart Caching**: Results are cached to avoid repeated analysis of the same files
- **File Type Detection**: Automatically detects video files (.mp4, .mkv, .avi, .mov, .wmv, .flv, .webm, .m4v)
- **Docker & Koyeb Compatible**: Optimized for containerized deployments

## 🔧 Configuration

### Environment Variable
Add this to your environment variables or `.env` file:

```bash
# Enable/Disable Media Info Feature (default: True)
ENABLE_MEDIA_INFO=True
```

### Options:
- `True` - Enable media info buttons for video files
- `False` - Disable media info feature completely

## 🚀 How It Works

1. **File Listing**: When users search for movies/videos, each video file will have an additional "📊 Media Info" button
2. **On-Demand Processing**: Only when a user clicks this button, the bot analyzes the file
3. **Quick Response**: Analysis is done in real-time with a loading message
4. **Detailed Information**: Users get comprehensive media details including:
   - 📦 File size
   - ⏱️ Duration
   - 📡 Bitrate
   - 🎥 Video codec (H.264, H.265, etc.)
   - 📐 Resolution (1080p, 720p, etc.)
   - 🎞️ Frame rate
   - 🔊 Audio codec
   - 📻 Audio channels
   - 🎼 Sample rate
   - 💬 Subtitle tracks (if available)

## 📱 User Experience

### Before clicking Media Info:
```
📁 Movie.2023.1080p.x264.mkv [2.1 GB]
📊 Media Info
```

### After clicking Media Info:
```
📊 Media Information
📁 File: Movie.2023.1080p.x264.mkv

📦 Size: 2.1 GB
⏱️ Duration: 02:15:30
📡 Bitrate: 2500 kbps

🎬 Video Information:
🎥 Codec: H264
📐 Resolution: 1920x1080
🎞️ Frame Rate: 23.98 fps

🎵 Audio Information:
🔊 Codec: AAC
📻 Channels: 2
🎼 Sample Rate: 48000 Hz

💬 Subtitle Tracks: 2
   1. English (srt)
   2. Spanish (srt)

⚡ Analysis completed in real-time
```

## 🐳 Docker Deployment

The feature is fully compatible with Docker and Koyeb. The `ffmpeg` and `ffmpeg-python` dependencies are already included in the requirements.

### Docker Environment Variables:
```bash
# Add to your docker-compose.yml or Koyeb environment
ENABLE_MEDIA_INFO=True
```

## ⚡ Performance Optimization

- **Lazy Loading**: Media analysis only happens on user request
- **Caching System**: Previously analyzed files are cached in memory
- **Filename Analysis**: For Telegram bots, the system intelligently extracts info from filenames
- **Async Processing**: Non-blocking analysis doesn't affect other bot operations
- **Resource Efficient**: Minimal server load since analysis is user-triggered

## 🔒 Privacy & Security

- No files are permanently stored on the server
- Analysis is done on metadata only
- Cache is cleared periodically to save memory
- All processing happens server-side securely

## 🛠️ Technical Details

### Supported File Formats:
- MP4, MKV, AVI, MOV, WMV, FLV, WebM, M4V

### Dependencies:
- `ffmpeg-python` - For media analysis
- `ffmpeg` - Core media processing
- Standard bot dependencies

### File Structure:
```
plugins/
├── media_info.py          # New media info handler
├── pm_filter.py           # Modified to include media info buttons
└── ...

info.py                    # Added ENABLE_MEDIA_INFO configuration
requirements.txt           # Includes ffmpeg dependencies
```

## 🚫 Troubleshooting

### Media Info button not showing:
1. Check `ENABLE_MEDIA_INFO=True` in environment
2. Ensure file is a supported video format
3. Restart the bot after configuration changes

### Analysis fails:
1. Verify ffmpeg is installed in container
2. Check file permissions
3. Ensure sufficient memory for analysis

### Performance issues:
1. Consider disabling for very large deployments
2. Monitor memory usage with caching
3. Adjust cache timeout if needed

## 📈 Future Enhancements

- Custom analysis templates
- Audio-only file support
- Image metadata extraction
- Performance metrics dashboard
- User preference settings

---

**Note**: This feature is designed to enhance user experience while maintaining optimal server performance. The on-demand nature ensures your bot remains fast and responsive for all users.