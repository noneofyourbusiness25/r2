import asyncio
import json
import tempfile
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MediaInfoExtractor:
    def __init__(self):
        self.info_cache = {}  # Temporary cache for media info
        
    async def download_file_chunk(self, client, file_id: str, chunk_size: int = 2*1024*1024) -> Optional[str]:
        """Download first chunk of file for analysis"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download first 2MB for media analysis (usually sufficient for headers)
            downloaded = 0
            async for chunk in client.stream_media(file_id, limit=chunk_size):
                with open(temp_path, 'ab') as f:
                    f.write(chunk)
                downloaded += len(chunk)
                if downloaded >= chunk_size:
                    break
                
            # Check if file is large enough for analysis
            if downloaded < 1024:  # Less than 1KB
                return None
                
            return temp_path
        except Exception as e:
            logger.error(f"Error downloading file chunk: {e}")
            return None
    
    async def extract_media_info(self, client, file_id: str, file_name: str = "") -> Optional[Dict[str, Any]]:
        """Extract media information using ffprobe"""
        
        # Check cache first
        if file_id in self.info_cache:
            return self.info_cache[file_id]
        
        # Quick check if file might be media based on extension
        if file_name:
            ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
            media_extensions = {
                'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', '3gp',
                'mp3', 'flac', 'aac', 'ogg', 'wma', 'wav', 'm4a', 'opus'
            }
            if ext not in media_extensions:
                # For non-media files, return basic info
                return {
                    'format': ext.upper() if ext else 'Unknown',
                    'duration': 'N/A',
                    'size': 'Unknown',
                    'audio_tracks': [],
                    'video_info': None,
                    'subtitle_tracks': [],
                    'bitrate': 'N/A'
                }
            
        temp_path = None
        try:
            # Download file chunk for analysis
            temp_path = await self.download_file_chunk(client, file_id)
            if not temp_path:
                return None
                
            # Use ffprobe to extract media info
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                '-show_format', '-show_streams', temp_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"ffprobe error: {stderr.decode()}")
                return None
                
            probe_data = json.loads(stdout.decode())
            media_info = self._parse_probe_data(probe_data, file_name)
            
            # Cache the result temporarily (5 minutes)
            self.info_cache[file_id] = media_info
            
            # Clean cache after 5 minutes
            asyncio.create_task(self._clean_cache_after_delay(file_id, 300))
            
            return media_info
            
        except Exception as e:
            logger.error(f"Error extracting media info: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def _parse_probe_data(self, probe_data: Dict, file_name: str) -> Dict[str, Any]:
        """Parse ffprobe output into readable format"""
        info = {
            'format': 'Unknown',
            'duration': 'Unknown',
            'size': 'Unknown',
            'audio_tracks': [],
            'video_info': None,
            'subtitle_tracks': [],
            'bitrate': 'Unknown'
        }
        
        try:
            format_info = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            # Format and container
            if 'format_name' in format_info:
                info['format'] = format_info['format_name'].upper()
            elif file_name:
                info['format'] = file_name.split('.')[-1].upper() if '.' in file_name else 'Unknown'
            
            # Duration
            if 'duration' in format_info:
                duration_sec = float(format_info['duration'])
                info['duration'] = self._format_duration(duration_sec)
            
            # File size
            if 'size' in format_info:
                size_bytes = int(format_info['size'])
                info['size'] = self._format_size(size_bytes)
            
            # Bitrate
            if 'bit_rate' in format_info:
                bitrate = int(format_info['bit_rate'])
                info['bitrate'] = f"{bitrate // 1000} kbps" if bitrate > 0 else 'Unknown'
            
            # Analyze streams
            audio_count = 0
            video_count = 0
            subtitle_count = 0
            
            for stream in streams:
                codec_type = stream.get('codec_type', '')
                
                if codec_type == 'audio':
                    audio_count += 1
                    audio_info = {
                        'index': stream.get('index', audio_count),
                        'codec': stream.get('codec_name', 'Unknown'),
                        'language': stream.get('tags', {}).get('language', 'und'),
                        'title': stream.get('tags', {}).get('title', f'Audio {audio_count}'),
                        'channels': stream.get('channels', 'Unknown'),
                        'sample_rate': stream.get('sample_rate', 'Unknown')
                    }
                    info['audio_tracks'].append(audio_info)
                    
                elif codec_type == 'video' and video_count == 0:
                    video_count += 1
                    info['video_info'] = {
                        'codec': stream.get('codec_name', 'Unknown'),
                        'width': stream.get('width', 'Unknown'),
                        'height': stream.get('height', 'Unknown'),
                        'fps': stream.get('r_frame_rate', 'Unknown')
                    }
                    
                elif codec_type == 'subtitle':
                    subtitle_count += 1
                    subtitle_info = {
                        'index': stream.get('index', subtitle_count),
                        'codec': stream.get('codec_name', 'Unknown'),
                        'language': stream.get('tags', {}).get('language', 'und'),
                        'title': stream.get('tags', {}).get('title', f'Subtitle {subtitle_count}')
                    }
                    info['subtitle_tracks'].append(subtitle_info)
            
        except Exception as e:
            logger.error(f"Error parsing probe data: {e}")
        
        return info
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human readable format"""
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {secs}s"
            elif minutes > 0:
                return f"{minutes}m {secs}s"
            else:
                return f"{secs}s"
        except:
            return "Unknown"
    
    def _format_size(self, bytes_size: int) -> str:
        """Format file size in human readable format"""
        try:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.1f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.1f} PB"
        except:
            return "Unknown"
    
    async def _clean_cache_after_delay(self, file_id: str, delay: int):
        """Clean cache entry after specified delay"""
        await asyncio.sleep(delay)
        self.info_cache.pop(file_id, None)
    
    def format_media_info_message(self, media_info: Dict[str, Any], file_name: str) -> str:
        """Format media info into a readable message"""
        if not media_info:
            return "❌ Could not extract media information"
        
        message = f"📋 <b>Media Information</b>\n\n"
        message += f"📁 <b>File:</b> <code>{file_name}</code>\n"
        message += f"📦 <b>Format:</b> {media_info.get('format', 'Unknown')}\n"
        message += f"⏱ <b>Duration:</b> {media_info.get('duration', 'Unknown')}\n"
        message += f"📏 <b>Size:</b> {media_info.get('size', 'Unknown')}\n"
        message += f"🔗 <b>Bitrate:</b> {media_info.get('bitrate', 'Unknown')}\n\n"
        
        # Video info
        video_info = media_info.get('video_info')
        if video_info:
            message += f"🎬 <b>Video:</b> {video_info.get('codec', 'Unknown')} "
            if video_info.get('width') != 'Unknown' and video_info.get('height') != 'Unknown':
                message += f"({video_info['width']}x{video_info['height']})\n"
            else:
                message += "\n"
        
        # Audio tracks
        audio_tracks = media_info.get('audio_tracks', [])
        if audio_tracks:
            message += f"🔊 <b>Audio Tracks:</b> {len(audio_tracks)}\n"
            for i, audio in enumerate(audio_tracks[:3]):  # Show max 3 tracks
                lang = audio.get('language', 'und')
                title = audio.get('title', f'Track {i+1}')
                codec = audio.get('codec', 'Unknown')
                channels = audio.get('channels', 'Unknown')
                message += f"   • {title} ({lang}) - {codec}"
                if channels != 'Unknown':
                    message += f" - {channels}ch"
                message += "\n"
            if len(audio_tracks) > 3:
                message += f"   • ... and {len(audio_tracks) - 3} more\n"
        
        # Subtitle tracks
        subtitle_tracks = media_info.get('subtitle_tracks', [])
        if subtitle_tracks:
            message += f"💬 <b>Subtitles:</b> {len(subtitle_tracks)}\n"
            for i, sub in enumerate(subtitle_tracks[:3]):  # Show max 3 tracks
                lang = sub.get('language', 'und')
                title = sub.get('title', f'Subtitle {i+1}')
                message += f"   • {title} ({lang})\n"
            if len(subtitle_tracks) > 3:
                message += f"   • ... and {len(subtitle_tracks) - 3} more\n"
        
        return message

# Global instance
media_extractor = MediaInfoExtractor()