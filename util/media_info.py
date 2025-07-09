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
        
    async def download_file_chunk(self, client, file_id: str, chunk_size: int = 3*1024*1024) -> Optional[str]:
        """Download first chunk of file for analysis"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download first 3MB for media analysis using Pyrogram's download_media
            # We'll download to the temp file and then truncate if needed
            try:
                downloaded_path = await client.download_media(
                    file_id, 
                    file_name=temp_path,
                    block=False
                )
                
                if not downloaded_path or not os.path.exists(temp_path):
                    logger.error("File download failed")
                    return None
                
                # Check file size and truncate if it's too large for analysis
                file_size = os.path.getsize(temp_path)
                
                if file_size > chunk_size:
                    # Read only the first chunk for analysis
                    with open(temp_path, 'rb') as f:
                        chunk_data = f.read(chunk_size)
                    
                    # Write only the chunk back to the temp file
                    with open(temp_path, 'wb') as f:
                        f.write(chunk_data)
                
                # Check if file is large enough for analysis
                final_size = os.path.getsize(temp_path)
                if final_size < 1024:  # Less than 1KB
                    logger.warning(f"Downloaded file too small: {final_size} bytes")
                    return None
                
                logger.info(f"Downloaded {final_size} bytes for analysis")
                return temp_path
                
            except Exception as download_error:
                logger.error(f"Download failed: {download_error}")
                # Try alternative download approach
                return await self._alternative_download(client, file_id, temp_path, chunk_size)
                
        except Exception as e:
            logger.error(f"Error in download_file_chunk: {e}")
            return None
    
    async def _alternative_download(self, client, file_id: str, temp_path: str, chunk_size: int) -> Optional[str]:
        """Alternative download method using iter_download"""
        try:
            downloaded = 0
            with open(temp_path, 'wb') as f:
                async for chunk in client.iter_download(file_id):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded >= chunk_size:
                        break
            
            if downloaded < 1024:
                return None
                
            return temp_path
        except Exception as e:
            logger.error(f"Alternative download failed: {e}")
            return None
    
    async def extract_media_info(self, client, file_id: str, file_name: str = "") -> Optional[Dict[str, Any]]:
        """Extract media information using ffprobe"""
        
        # Check cache first
        if file_id in self.info_cache:
            logger.info(f"Using cached info for {file_id}")
            return self.info_cache[file_id]
        
        logger.info(f"Starting media info extraction for: {file_name}")
        
        temp_path = None
        try:
            # Download file chunk for analysis
            logger.info("Downloading file chunk for analysis...")
            temp_path = await self.download_file_chunk(client, file_id)
            if not temp_path:
                logger.error("Failed to download file chunk")
                return self._get_basic_info(file_name)
                
            # Try ffprobe first, fallback to basic analysis
            logger.info("Attempting ffprobe analysis...")
            
            # First try ffprobe
            try:
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                    '-show_format', '-show_streams', '-show_chapters', temp_path
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    try:
                        probe_data = json.loads(stdout.decode())
                        logger.info("Successfully used ffprobe for analysis")
                        media_info = self._parse_probe_data(probe_data, file_name)
                        
                        # Cache the result temporarily (5 minutes)
                        self.info_cache[file_id] = media_info
                        logger.info(f"Cached detailed media info for {file_id}")
                        
                        # Clean cache after 5 minutes
                        asyncio.create_task(self._clean_cache_after_delay(file_id, 300))
                        
                        return media_info
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse ffprobe output: {e}")
                else:
                    error_msg = stderr.decode() if stderr else "ffprobe failed"
                    logger.warning(f"ffprobe failed: {error_msg}")
                    
            except FileNotFoundError:
                logger.warning("ffprobe not found, using fallback mode")
            except Exception as e:
                logger.warning(f"ffprobe error: {e}, using fallback mode")
            
            # Fallback to basic file analysis
            logger.info("Using fallback mode for media analysis")
            media_info = await self._analyze_with_pyrogram(client, file_id, file_name, temp_path)
            
            # Cache the result temporarily (5 minutes)
            self.info_cache[file_id] = media_info
            logger.info(f"Cached basic media info for {file_id}")
            
            # Clean cache after 5 minutes
            asyncio.create_task(self._clean_cache_after_delay(file_id, 300))
            
            return media_info
            
        except Exception as e:
            logger.error(f"Error extracting media info: {e}")
            return self._get_basic_info(file_name)
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.info("Cleaned up temporary file")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file: {cleanup_error}")
    
    async def _analyze_with_pyrogram(self, client, file_id: str, file_name: str, temp_path: str) -> Dict[str, Any]:
        """Fallback analysis using Pyrogram and basic file info"""
        try:
            # Get file info from database
            from database.ia_filterdb import get_file_details
            files_ = await get_file_details(file_id)
            
            if files_:
                file_info = files_[0]
                file_size = getattr(file_info, 'file_size', 0)
                mime_type = getattr(file_info, 'mime_type', '')
                
                # Basic file analysis
                ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
                
                # Try to determine format from extension and mime type
                format_name = self._get_format_from_extension(ext, mime_type)
                
                # Get file size from temp file if available
                if temp_path and os.path.exists(temp_path):
                    temp_size = os.path.getsize(temp_path)
                    size_str = self._format_size(file_size) if file_size > 0 else self._format_size(temp_size)
                else:
                    size_str = self._format_size(file_size) if file_size > 0 else 'Unknown'
                
                return {
                    'format': format_name,
                    'duration': 'Not Available (Install ffmpeg for duration)',
                    'size': size_str,
                    'audio_tracks': self._guess_audio_tracks(file_name, mime_type),
                    'video_info': self._guess_video_info(file_name, mime_type),
                    'subtitle_tracks': self._guess_subtitle_tracks(file_name),
                    'bitrate': 'Not Available (Install ffmpeg for bitrate)',
                    'chapters': [],
                    'note': 'Limited info - Install ffmpeg for detailed analysis'
                }
            else:
                return self._get_basic_info(file_name)
                
        except Exception as e:
            logger.error(f"Error in Pyrogram analysis: {e}")
            return self._get_basic_info(file_name)
    
    def _get_format_from_extension(self, ext: str, mime_type: str) -> str:
        """Determine format from file extension and mime type"""
        if mime_type:
            if 'video/mp4' in mime_type:
                return 'MP4'
            elif 'video/x-matroska' in mime_type:
                return 'MATROSKA/MKV'
            elif 'video/x-msvideo' in mime_type:
                return 'AVI'
            elif 'audio/mpeg' in mime_type:
                return 'MP3'
            elif 'audio/flac' in mime_type:
                return 'FLAC'
        
        # Fallback to extension
        ext_formats = {
            'mp4': 'MP4',
            'mkv': 'MATROSKA/MKV', 
            'avi': 'AVI',
            'mov': 'QuickTime/MOV',
            'wmv': 'WMV',
            'flv': 'FLV',
            'webm': 'WebM',
            'mp3': 'MP3',
            'flac': 'FLAC',
            'aac': 'AAC',
            'ogg': 'OGG'
        }
        
        return ext_formats.get(ext.lower(), ext.upper() if ext else 'Unknown')
    
    def _guess_audio_tracks(self, file_name: str, mime_type: str) -> list:
        """Guess audio tracks from filename patterns"""
        tracks = []
        
        # Common audio indicators in filenames
        audio_patterns = {
            'hindi': ('Hindi', 'hin'),
            'english': ('English', 'eng'),
            'tamil': ('Tamil', 'tam'),
            'telugu': ('Telugu', 'tel'),
            'dual': ('Dual Audio', 'mul'),
            'multi': ('Multi Audio', 'mul')
        }
        
        filename_lower = file_name.lower()
        
        for pattern, (title, lang) in audio_patterns.items():
            if pattern in filename_lower:
                tracks.append({
                    'title': title,
                    'language': lang,
                    'codec': 'Unknown',
                    'channels': 'Unknown'
                })
        
        # If no specific patterns found, assume single track
        if not tracks:
            tracks.append({
                'title': 'Audio Track',
                'language': 'und',
                'codec': 'Unknown',
                'channels': 'Unknown'
            })
        
        return tracks
    
    def _guess_video_info(self, file_name: str, mime_type: str) -> dict:
        """Guess video info from filename patterns"""
        if 'audio' in mime_type.lower() or any(ext in file_name.lower() for ext in ['.mp3', '.flac', '.aac', '.ogg']):
            return None
        
        # Resolution patterns
        if '1080p' in file_name or '1080' in file_name:
            return {'codec': 'Unknown', 'width': 1920, 'height': 1080}
        elif '720p' in file_name or '720' in file_name:
            return {'codec': 'Unknown', 'width': 1280, 'height': 720}
        elif '480p' in file_name or '480' in file_name:
            return {'codec': 'Unknown', 'width': 854, 'height': 480}
        elif '4k' in file_name.lower() or '2160p' in file_name:
            return {'codec': 'Unknown', 'width': 3840, 'height': 2160}
        else:
            return {'codec': 'Unknown', 'width': 'Unknown', 'height': 'Unknown'}
    
    def _guess_subtitle_tracks(self, file_name: str) -> list:
        """Guess subtitle availability from filename"""
        subs = []
        
        # Common subtitle indicators
        if any(pattern in file_name.lower() for pattern in ['subtitle', 'sub', 'srt']):
            subs.append({
                'title': 'Subtitles',
                'language': 'eng',
                'codec': 'Unknown'
            })
        
        return subs
    
    def _get_basic_info(self, file_name: str) -> Dict[str, Any]:
        """Get basic file info when media analysis fails"""
        ext = file_name.lower().split('.')[-1] if '.' in file_name and file_name else ''
        return {
            'format': ext.upper() if ext else 'Unknown',
            'duration': 'Analysis Failed',
            'size': 'Unknown',
            'audio_tracks': [],
            'video_info': None,
            'subtitle_tracks': [],
            'bitrate': 'Unknown',
            'chapters': []
        }
    
    def _parse_probe_data(self, probe_data: Dict, file_name: str) -> Dict[str, Any]:
        """Parse ffprobe output into readable format"""
        info = {
            'format': 'Unknown',
            'duration': 'Unknown',
            'size': 'Unknown',
            'audio_tracks': [],
            'video_info': None,
            'subtitle_tracks': [],
            'bitrate': 'Unknown',
            'chapters': []
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
            
            # Chapters
            chapters = probe_data.get('chapters', [])
            if chapters:
                info['chapters'] = []
                for chapter in chapters[:5]:  # Show first 5 chapters
                    chapter_info = {
                        'title': chapter.get('tags', {}).get('title', f"Chapter {chapter.get('id', '?')}"),
                        'start_time': chapter.get('start_time', '0'),
                        'end_time': chapter.get('end_time', '0')
                    }
                    info['chapters'].append(chapter_info)
            
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
        message += f"🔗 <b>Bitrate:</b> {media_info.get('bitrate', 'Unknown')}\n"
        
        # Show note if using fallback mode
        if 'note' in media_info:
            message += f"\n💡 <i>{media_info['note']}</i>\n"
        
        message += "\n"
        
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
                codec = sub.get('codec', 'Unknown')
                message += f"   • {title} ({lang}) - {codec}\n"
            if len(subtitle_tracks) > 3:
                message += f"   • ... and {len(subtitle_tracks) - 3} more\n"
        
        # Chapters
        chapters = media_info.get('chapters', [])
        if chapters:
            message += f"\n📖 <b>Chapters:</b> {len(chapters)}"
            if len(chapters) > 5:
                message += f" (showing first 5)"
            message += "\n"
            for chapter in chapters[:3]:  # Show first 3 chapters
                title = chapter.get('title', 'Untitled')
                start_time = self._format_timestamp(chapter.get('start_time', '0'))
                message += f"   • {title} - {start_time}\n"
            if len(chapters) > 3:
                message += f"   • ... and {len(chapters) - 3} more\n"
        
        return message
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp from seconds to readable format"""
        try:
            seconds = float(timestamp_str)
            return self._format_duration(seconds)
        except:
            return timestamp_str

# Global instance
media_extractor = MediaInfoExtractor()