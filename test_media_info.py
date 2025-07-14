#!/usr/bin/env python3
"""
Test script for Media Info functionality
Run this to verify that the media info feature is working correctly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

try:
    from plugins.media_info import simulate_media_analysis, format_media_info
    print("✅ Successfully imported media_info module")
except ImportError as e:
    print(f"❌ Failed to import media_info module: {e}")
    sys.exit(1)

async def test_media_info():
    """Test the media info functionality with sample data"""
    
    print("\n🧪 Testing Media Info Functionality\n")
    
    # Test cases with different file types and sizes
    test_cases = [
        {
            'name': 'Avatar.2009.1080p.BluRay.x264.mkv',
            'size': 2147483648,  # 2GB
            'description': 'High quality 1080p movie'
        },
        {
            'name': 'Series.S01E01.720p.HEVC.mp4',
            'size': 524288000,   # 500MB
            'description': 'TV series episode'
        },
        {
            'name': 'Documentary.4K.x265.webm',
            'size': 4294967296,  # 4GB
            'description': '4K documentary'
        },
        {
            'name': 'sample.480p.avi',
            'size': 104857600,   # 100MB
            'description': 'Lower quality video'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 Test Case {i}: {test_case['description']}")
        print(f"   File: {test_case['name']}")
        print(f"   Size: {test_case['size']} bytes")
        
        try:
            # Test the analysis function
            media_info = await simulate_media_analysis(
                test_case['name'], 
                test_case['size']
            )
            
            if media_info:
                print("   ✅ Analysis successful")
                
                # Test the formatting function
                formatted_info = format_media_info(media_info, test_case['name'])
                
                if formatted_info:
                    print("   ✅ Formatting successful")
                    print("   📋 Sample output:")
                    # Show first few lines of the formatted output
                    lines = formatted_info.split('\n')[:8]
                    for line in lines:
                        print(f"      {line}")
                    print("      ...")
                else:
                    print("   ❌ Formatting failed")
            else:
                print("   ❌ Analysis failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

def test_configuration():
    """Test configuration imports"""
    print("🔧 Testing Configuration\n")
    
    try:
        from info import ENABLE_MEDIA_INFO
        print(f"✅ ENABLE_MEDIA_INFO = {ENABLE_MEDIA_INFO}")
    except ImportError:
        print("❌ Failed to import ENABLE_MEDIA_INFO from info.py")
        return False
    
    # Test ffmpeg availability
    try:
        import ffmpeg
        print("✅ ffmpeg-python module available")
    except ImportError:
        print("❌ ffmpeg-python module not available")
        return False
    
    return True

def test_file_detection():
    """Test file type detection logic"""
    print("🎬 Testing File Type Detection\n")
    
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
    test_files = [
        'movie.mp4',
        'series.mkv', 
        'clip.avi',
        'video.mov',
        'recording.wmv',
        'stream.flv',
        'web.webm',
        'mobile.m4v',
        'audio.mp3',  # Should not match
        'document.pdf'  # Should not match
    ]
    
    for filename in test_files:
        is_video = any(ext in filename.lower() for ext in video_extensions)
        status = "✅ Video" if is_video else "❌ Not Video"
        print(f"   {filename}: {status}")

async def main():
    """Main test function"""
    print("🚀 Media Info Feature Test Suite")
    print("=" * 50)
    
    # Test configuration first
    if not test_configuration():
        print("\n❌ Configuration test failed. Please check your setup.")
        return
    
    print()
    
    # Test file detection
    test_file_detection()
    
    print()
    
    # Test media info functionality
    await test_media_info()
    
    print("🎉 All tests completed!")
    print("\n💡 Tips:")
    print("   - Set ENABLE_MEDIA_INFO=True in your environment")
    print("   - Ensure ffmpeg is installed in your Docker container")
    print("   - Restart your bot after configuration changes")

if __name__ == "__main__":
    asyncio.run(main())