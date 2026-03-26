"""
TikTok downloader implementation
Supports: Individual TikTok videos and photo posts (with audio extraction)
"""
import re
import yt_dlp
from .base_downloader import BaseDownloader
from ..data_models import VideoInfo
from ..utils.settings_manager import SettingsManager


class TikTokDownloader(BaseDownloader):
    """Downloader for TikTok videos and photo posts"""
    
    def canHandle(self, url: str) -> bool:
        """Check if URL is from TikTok"""
        patterns = [r'tiktok\.com/', r'vm\.tiktok\.com/', r'vt\.tiktok\.com/']
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def isPlaylist(self, url: str) -> bool:
        """Check if URL is a user profile"""
        return bool(re.search(r'tiktok\.com/@[^/]+/?$', url, re.IGNORECASE))
    
    def _isPhotoPost(self, url: str) -> bool:
        """Check if URL is a photo/slideshow post"""
        return '/photo/' in url.lower() or 'aweme_type=150' in url
    
    def getVideoInfo(self, url: str) -> VideoInfo:
        """Fetch TikTok video/photo post information"""
        is_photo_post = self._isPhotoPost(url)
        
        ydl_opts = {'quiet': True, 'no_warnings': True, 'nocheckcertificate': True}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check if it's a photo post with audio
                if is_photo_post:
                    return VideoInfo(
                        title=info.get('title', 'TikTok Photo Post'),
                        duration=self._formatDuration(info.get('duration', 0)),
                        thumbnail=info.get('thumbnail', ''),
                        formats=['audio only']  # Photo posts only support audio extraction
                    )
                
                # Regular video post
                return VideoInfo(
                    title=info.get('title', 'TikTok Video'),
                    duration=self._formatDuration(info.get('duration', 0)),
                    thumbnail=info.get('thumbnail', ''),
                    formats=['best', '720p', '480p']
                )
        except Exception as e:
            error_msg = str(e)
            
            # Better error handling
            if "Unsupported URL" in error_msg:
                raise Exception(
                    "This TikTok post cannot be processed.\n\n"
                    "If it's a photo post:\n"
                    "• Try selecting MP3 format to extract the background music\n"
                    "• Video format won't work for photo posts\n\n"
                    "If it's a video:\n"
                    "• Make sure the link is valid and public"
                )
            else:
                raise Exception(f"Failed to fetch TikTok content: {error_msg}")
    
    def downloadVideo(self, url: str, outputPath: str, quality: str, 
                      formatType: str, progressCallback, title: str = None):
        """Download TikTok video or extract audio from photo posts"""
        is_photo_post = self._isPhotoPost(url)
        
        # For photo posts, force MP3 extraction
        if is_photo_post and formatType != 'MP3':
            raise Exception(
                "📸 This is a TikTok photo post (slideshow with music).\n\n"
                "Photo posts cannot be downloaded as video.\n"
                "However, you can extract the background music!\n\n"
                "💡 Solution: Select 'Audio (MP3)' format and try again."
            )
        
        ydl_opts = self._buildYdlOpts(outputPath, quality, formatType, progressCallback, is_photo_post, title)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            error_msg = str(e)
            if "Unsupported URL" in error_msg and is_photo_post:
                raise Exception(
                    "Cannot download this TikTok photo post.\n\n"
                    "Try selecting MP3 format to extract the music."
                )
            else:
                raise Exception(f"TikTok download failed: {error_msg}")
    
    def getProviderName(self) -> str:
        return "TikTok"
    
    def getDefaultFormats(self) -> list:
        return ['best', '720p', '480p']
    
    def _buildYdlOpts(self, outputPath, quality, formatType, progressCallback, is_photo_post=False, title: str = None):
        """Build yt-dlp options"""

        if title:
            outtmpl = f'{outputPath}/{title}.%(ext)s'
        else:
            outtmpl = f'{outputPath}/%(title)s.%(ext)s'

        base_opts = {
            'outtmpl': outtmpl,
            'progress_hooks': [progressCallback],
            'concurrent_fragment_downloads': SettingsManager.getMaxConcurrentParts(),
            'nocheckcertificate': True,
        }
        
        # For photo posts or MP3 format, extract audio
        if formatType == 'MP3' or is_photo_post:
            base_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        else:
            # Regular video download
            base_opts.update({
                'format': self._getFormatString(quality),
                'merge_output_format': 'mp4',
            })
        
        return base_opts
    
    def _formatDuration(self, seconds):
        """Convert seconds to readable duration"""
        if not seconds:
            return "00:00"
        minutes, secs = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _getFormatString(self, quality):
        """Convert quality to yt-dlp format string"""
        quality_map = {
            'best': 'bestvideo+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        }
        return quality_map.get(quality, 'bestvideo+bestaudio/best')