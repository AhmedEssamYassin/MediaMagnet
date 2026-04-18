"""
Download management functionality using Factory Pattern
"""

from ..data_models import VideoInfo
from ..downloaders import DownloaderFactory


class DownloadManager:
    """
    Handles video download operations using appropriate provider
    """
    
    @staticmethod
    def getVideoInfo(url: str) -> VideoInfo:
        """
        Fetch video information using appropriate downloader
        
        Args:
            url: Video URL
            
        Returns:
            VideoInfo object
            
        Raises:
            Exception: If no downloader supports the URL or fetch fails
        """
        downloader = DownloaderFactory.getDownloader(url)
        
        if not downloader:
            supported = ", ".join(DownloaderFactory.getSupportedProviders())
            raise Exception(
                f"Unsupported video URL. Supported providers: {supported}"
            )
        
        try:
            return downloader.getVideoInfo(url)
        except Exception as e:
            provider = downloader.getProviderName()
            raise Exception(f"{provider} - {str(e)}")
    
    @staticmethod
    def downloadVideo(url: str, outputPath: str, quality: str, 
                      formatType: str, progressCallback, title: str = None):
        """
        Download video using appropriate downloader
        
        Args:
            url: Video URL
            outputPath: Directory to save the video
            quality: Video quality
            formatType: Output format ('MP4' or 'MP3')
            progressCallback: Progress update callback
            title: Optional custom title for the video  
            
        Raises:
            Exception: If no downloader supports the URL or download fails
        """
        downloader = DownloaderFactory.getDownloader(url)
        
        if not downloader:
            supported = ", ".join(DownloaderFactory.getSupportedProviders())
            raise Exception(
                f"Unsupported video URL. Supported providers: {supported}"
            )
        
        try:
            downloader.downloadVideo(url, outputPath, quality, formatType, progressCallback, title)
        except Exception as e:
            provider = downloader.getProviderName()
            raise Exception(f"{provider} - {str(e)}")
    
    @staticmethod
    def getProviderForUrl(url: str) -> str:
        """
        Get the provider name for a given URL
        
        Args:
            url: Video URL
            
        Returns:
            Provider name or "Unknown"
        """
        downloader = DownloaderFactory.getDownloader(url)
        return downloader.getProviderName() if downloader else "Unknown"
    
    @staticmethod
    def isUrlSupported(url: str) -> bool:
        """
        Check if URL is supported by any downloader
        
        Args:
            url: Video URL to check
            
        Returns:
            True if supported
        """
        return DownloaderFactory.isSupported(url)