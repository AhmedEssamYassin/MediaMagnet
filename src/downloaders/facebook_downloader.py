"""
Facebook downloader implementation
"""

import os
import re
import yt_dlp
from .base_downloader import BaseDownloader
from ..data_models import VideoInfo
from ..utils.settings_manager import SettingsManager


class FacebookDownloader(BaseDownloader):
    """Facebook video downloader implementation"""
    
    def canHandle(self, url: str) -> bool:
        """Check if URL is a Facebook video"""
        facebookPatterns = [
            r'(https?://)?(www\.)?facebook\.com/',
            r'fb\.watch/',
            r'facebook\.com/watch',
            r'facebook\.com/.*/(videos|posts)/'
        ]
        return any(re.search(pattern, url) for pattern in facebookPatterns)
    
    def getVideoInfo(self, url: str) -> VideoInfo:
        """Fetch Facebook video information"""
        ydlOpts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydlOpts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Facebook videos typically have specific formats
                formats = []
                if 'formats' in info:
                    for f in info['formats']:
                        height = f.get('height')
                        if height:
                            formats.append(f"{height}p")
                
                # Remove duplicates and sort
                formats = sorted(list(set(formats)), 
                               key=lambda x: int(x.replace('p', '')),
                               reverse=True)
                
                # Format duration correctly
                durationSecs = info.get('duration') or 0
                mins, secs = divmod(int(durationSecs), 60)
                hours, mins = divmod(mins, 60)
                formattedDuration = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"
 
                return VideoInfo(
                    title=info.get('title', 'Facebook Video'),
                    duration=formattedDuration,
                    thumbnail=info.get('thumbnail', ''),
                    formats=formats if formats else ['best', '720p', '480p', '360p']
                )
        except Exception as e:
            raise Exception(f"Failed to fetch Facebook video info: {str(e)}")
    
    def downloadVideo(self, url: str, outputPath: str, quality: str, 
                      formatType: str, progressCallback, title: str = None):
        """Download Facebook video"""
        if title:
            outtmpl = os.path.join(outputPath, f'{title}.%(ext)s')
        else:
            outtmpl = os.path.join(outputPath, '%(title)s.%(ext)s')
        
        if formatType == "MP3":
            ydlOpts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [progressCallback],
                'concurrent_fragment_downloads': SettingsManager.getMaxConcurrentParts(),
            }
        else:
            if quality == 'best':
                formatString = 'best'
            else:
                height = quality.replace('p', '')
                formatString = f'best[height<={height}]/best'
            
            ydlOpts = {
                'format': formatString,
                'outtmpl': outtmpl,
                'progress_hooks': [progressCallback],
                'concurrent_fragment_downloads': SettingsManager.getMaxConcurrentParts(),
            }
        
        try:
            with yt_dlp.YoutubeDL(ydlOpts) as ydl:
                ydl.download([url])
        except Exception as e:
            raise Exception(f"Facebook download failed: {str(e)}")
    
    def getProviderName(self) -> str:
        """Get provider name"""
        return "Facebook"
    
    def getDefaultFormats(self) -> list:
        """Facebook-specific default formats"""
        return ['best', '720p', '480p', '360p']