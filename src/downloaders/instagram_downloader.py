"""
Instagram downloader implementation
Supports: posts, reels, and stories
"""

import re
import yt_dlp
from .base_downloader import BaseDownloader
from ..data_models import VideoInfo, PlaylistInfo
from ..utils.settings_manager import SettingsManager


class InstagramDownloader(BaseDownloader):
    """Downloader for Instagram content"""
    
    def canHandle(self, url: str) -> bool:
        """Check if URL is from Instagram"""
        patterns = [r'instagram\.com/', r'instagr\.am/']
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def isPlaylist(self, url: str) -> bool:
        """Instagram profile downloads not supported"""
        return False
    
    def getVideoInfo(self, url: str) -> VideoInfo:
        """Fetch Instagram video information"""
        ydlOpts = {'quiet': True, 'no_warnings': True, 'nocheckcertificate': True}
        
        try:
            with yt_dlp.YoutubeDL(ydlOpts) as ydl:
                info = ydl.extract_info(url, download=False)
                return VideoInfo(
                    title=info.get('title', 'Instagram Video'),
                    duration=self._formatDuration(info.get('duration', 0)),
                    thumbnail=info.get('thumbnail', ''),
                    formats=['best', '720p', '480p']
                )
        except Exception as e:
            raise Exception(f"Failed to fetch Instagram video: {str(e)}")
    
    def downloadVideo(self, url: str, outputPath: str, quality: str, 
                      formatType: str, progressCallback, title: str = None):
        """Download Instagram content"""
        ydlOpts = self._buildYdlOpts(outputPath, quality, formatType, progressCallback, title)
        
        try:
            with yt_dlp.YoutubeDL(ydlOpts) as ydl:
                ydl.download([url])
        except Exception as e:
            raise Exception(f"Instagram download failed: {str(e)}")
    
    def getProviderName(self) -> str:
        return "Instagram"
    
    def getDefaultFormats(self) -> list:
        return ['best', '720p', '480p']
    
    def _buildYdlOpts(self, outputPath, quality, formatType, progressCallback, title: str = None):
        """Build yt-dlp options"""

        if title:
            outtmpl = f'{outputPath}/{title}.%(ext)s'
        else:
            outtmpl = f'{outputPath}/%(title)s.%(ext)s'

        baseOpts = {
            'outtmpl': outtmpl,
            'progress_hooks': [progressCallback],
            'concurrent_fragment_downloads': SettingsManager.getMaxConcurrentParts(),
            'nocheckcertificate': True,
        }
        
        if formatType == 'MP3':
            baseOpts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        else:
            baseOpts.update({
                'format': self._getFormatString(quality),
                'merge_output_format': 'mp4',
            })
        
        return baseOpts
    
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
        qualityMap = {
            'best': 'bestvideo+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        }
        return qualityMap.get(quality, 'bestvideo+bestaudio/best')