"""
Factory for creating appropriate downloader based on URL
Implements Factory Pattern and Registry Pattern
"""

from typing import List, Optional
from .base_downloader import BaseDownloader
from .youtube_downloader import YouTubeDownloader
from .facebook_downloader import FacebookDownloader
from .instagram_downloader import InstagramDownloader
from .tiktok_downloader import TikTokDownloader   
from .twitter_downloader import TwitterDownloader   

class DownloaderFactory:
    """Factory for creating and managing video downloaders"""
    
    # Registry of available downloaders
    _downloaders: List[BaseDownloader] = []
    
    @classmethod
    def registerDownloader(cls, downloader: BaseDownloader):
        """
        Register a new downloader
        
        Args:
            downloader: Downloader instance to register
        """
        cls._downloaders.append(downloader)
    
    @classmethod
    def initializeDefaultDownloaders(cls):
        """Initialize and register default downloaders"""
        cls._downloaders.clear()
        cls.registerDownloader(YouTubeDownloader())
        cls.registerDownloader(FacebookDownloader())
        cls.registerDownloader(InstagramDownloader())
        cls.registerDownloader(TikTokDownloader())
        cls.registerDownloader(TwitterDownloader())
    
    @classmethod
    def getDownloader(cls, url: str) -> Optional[BaseDownloader]:
        """
        Get appropriate downloader for the given URL
        
        Args:
            url: Video URL
            
        Returns:
            Downloader instance that can handle the URL, or None
        """
        if not cls._downloaders:
            cls.initializeDefaultDownloaders()
        
        for downloader in cls._downloaders:
            if downloader.canHandle(url):
                return downloader
        
        return None
    
    @classmethod
    def getSupportedProviders(cls) -> List[str]:
        """
        Get list of supported provider names
        
        Returns:
            List of provider names
        """
        if not cls._downloaders:
            cls.initializeDefaultDownloaders()
        
        return [d.getProviderName() for d in cls._downloaders]
    
    @classmethod
    def isSupported(cls, url: str) -> bool:
        """
        Check if any downloader supports this URL
        
        Args:
            url: Video URL to check
            
        Returns:
            True if URL is supported
        """
        return cls.getDownloader(url) is not None


# Initialize default downloaders when module is imported
DownloaderFactory.initializeDefaultDownloaders()