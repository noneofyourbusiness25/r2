#!/usr/bin/env python3
"""
Quick debug script to check Media Info configuration
Run this to see why media info buttons might not be showing
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

def check_environment():
    """Check environment variables"""
    print("🔧 Environment Variables Check:")
    print("-" * 40)
    
    enable_media_info = os.environ.get('ENABLE_MEDIA_INFO', 'Not Set')
    print(f"ENABLE_MEDIA_INFO: {enable_media_info}")
    
    if enable_media_info == 'Not Set':
        print("❌ ENABLE_MEDIA_INFO is NOT set in environment!")
        print("   Add this to your Docker/Koyeb environment:")
        print("   ENABLE_MEDIA_INFO=True")
        return False
    
    if enable_media_info.lower() in ['true', '1', 'yes']:
        print("✅ ENABLE_MEDIA_INFO is enabled")
        return True
    else:
        print("❌ ENABLE_MEDIA_INFO is set but disabled")
        print(f"   Current value: {enable_media_info}")
        print("   Change it to: True")
        return False

def check_imports():
    """Check if imports work"""
    print("\n📦 Import Check:")
    print("-" * 40)
    
    try:
        from info import ENABLE_MEDIA_INFO
        print(f"✅ Successfully imported ENABLE_MEDIA_INFO: {ENABLE_MEDIA_INFO}")
        return True
    except Exception as e:
        print(f"❌ Failed to import ENABLE_MEDIA_INFO: {e}")
        return False

def check_file_detection():
    """Test file detection logic"""
    print("\n🎬 File Detection Test:")
    print("-" * 40)
    
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
    test_files = [
        'Movie.2023.1080p.x264.mkv',
        'Series.S01E01.720p.mp4',
        'Documentary.4K.avi',
        'Video.mov',
        'clip.wmv',
        'stream.flv',
        'web.webm',
        'mobile.m4v',
        'audio.mp3',  # Should NOT match
        'document.pdf'  # Should NOT match
    ]
    
    for filename in test_files:
        is_video = any(ext in filename.lower() for ext in video_extensions)
        status = "✅ Will show button" if is_video else "❌ No button"
        print(f"   {filename}: {status}")

def main():
    """Main debug function"""
    print("🔍 Media Info Button Debug Tool")
    print("=" * 50)
    
    env_ok = check_environment()
    import_ok = check_imports()
    
    check_file_detection()
    
    print("\n💡 Summary:")
    print("-" * 40)
    
    if env_ok and import_ok:
        print("✅ Configuration looks good!")
        print("\n🚀 Next steps:")
        print("   1. Restart your bot (docker container)")
        print("   2. Search for a movie with video files")
        print("   3. Look for '📊 Media Info' button under video files")
        print("   4. Check bot logs for debug messages")
    else:
        print("❌ Configuration issues found!")
        print("\n🔧 To fix:")
        if not env_ok:
            print("   1. Set ENABLE_MEDIA_INFO=True in your environment")
        if not import_ok:
            print("   2. Check your bot dependencies")
        print("   3. Restart your bot after making changes")
    
    print("\n📝 Need help?")
    print("   - Check bot logs when searching for videos")
    print("   - Look for 'Media Info Debug' messages")
    print("   - Test with files that have video extensions")

if __name__ == "__main__":
    main()