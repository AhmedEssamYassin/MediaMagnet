# pyre-ignore-all-errors
"""
YouTube downloader implementation
"""

import os
import re
import yt_dlp
from .base_downloader import BaseDownloader
from ..data_models import VideoInfo, PlaylistInfo
from ..utils.file_utils import getFfmpegPath
from ..utils.settings_manager import SettingsManager


class YouTubeDownloader(BaseDownloader):
    """YouTube video downloader implementation"""
    
    def canHandle(self, url: str) -> bool:
        """Check if URL is a YouTube video"""
        youtube_patterns = [
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/embed/',
            r'youtube\.com/v/'
        ]
        return any(re.search(pattern, url) for pattern in youtube_patterns)
    
    def getVideoInfo(self, url: str) -> VideoInfo:
        """Fetch YouTube video information"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'ffmpeg_location': getFfmpegPath(),
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:  # This is a playlist
                    videos = []
                    for entry in info['entries']:
                        if entry: # Ensure entry is not None
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            videos.append({'title': entry.get('title', 'N/A'), 'url': video_url})
                    return PlaylistInfo(title=info.get('title', 'N/A'), videos=videos)
                else:
                    formats = []
                    if 'formats' in info:
                        for f in info['formats']:
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                resolution = f.get('resolution', 'unknown')
                                if resolution != 'unknown' and 'audio only' not in resolution.lower():
                                    formats.append(resolution)
                    
                    formats = sorted(list(set(formats)), 
                                key=lambda x: int(x.split('x')[0]) if 'x' in x else 0,
                                reverse=True)
                    
                    duration_secs = info.get('duration', 0)
                    mins, secs = divmod(duration_secs, 60)
                    hours, mins = divmod(mins, 60)
                    formatted_duration = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours else f"{mins:02d}:{secs:02d}"
                    
                    thumbnail_url = info.get('thumbnail', '')
                    
                    return VideoInfo(
                        title=info.get('title', 'Unknown'),
                        duration=formatted_duration,
                        thumbnail=thumbnail_url,
                        formats=formats if formats else self.get_default_formats()
                    )
        except Exception as e:
            raise Exception(f"Failed to fetch YouTube video info: {str(e)}")
    
    def downloadVideo(self, url: str, outputPath: str, quality: str, 
                      formatType: str, progressCallback, title: str = None):
        """Download YouTube video"""
        
        if title:
            outtmpl = os.path.join(outputPath, f'{title}.%(ext)s')
        else:
            outtmpl = os.path.join(outputPath, '%(title)s.%(ext)s')

        if formatType == "MP3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [progressCallback],
                'ffmpeg_location': getFfmpegPath(),
                'concurrent_fragment_downloads': SettingsManager.getMaxConcurrentParts(),
            }
        else:
            ffmpegPath = getFfmpegPath()
            ffmpegAvailable = os.path.isfile(ffmpegPath)
            
            if quality == 'best':
                if ffmpegAvailable:
                    format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                else:
                    # Pre-merged format that doesn't need ffmpeg
                    format_string = 'best[ext=mp4]/best'
            else:
                height = quality.split('x')[-1].replace('p', '')
                if ffmpegAvailable:
                    format_string = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'
                else:
                    format_string = f'best[height<={height}][ext=mp4]/best[height<={height}]/best'
            
            ydl_opts = {
                'format': format_string,
                'outtmpl': outtmpl,
                'progress_hooks': [progressCallback],
                'ffmpeg_location': ffmpegPath,
                'concurrent_fragment_downloads': SettingsManager.getMaxConcurrentParts(),
            }
            
            if ffmpegAvailable:
                ydl_opts['merge_output_format'] = 'mp4'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            raise Exception(f"YouTube download failed: {str(e)}")
    
    def getProviderName(self) -> str:
        """Get provider name"""
        return "YouTube"