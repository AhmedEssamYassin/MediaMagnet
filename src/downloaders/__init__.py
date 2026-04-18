"""
Platform-specific video downloaders implementing OCP.

This module implements the Open/Closed Principle through an abstract
base class and concrete platform implementations. New platforms can be
added by creating new downloader classes without modifying existing code.

Architecture:
    - BaseDownloader: Abstract interface (contract)
    - Platform implementations: YouTube, Facebook, etc.
    - DownloaderFactory: Automatic platform detection and selection
"""

from typing import Optional  

__all__ = [
    "BaseDownloader",
    "YouTubeDownloader",
    "FacebookDownloader",
    "InstagramDownloader",
    "TikTokDownloader",
    "TwitterDownloader",
    "DownloaderFactory",
    "registerDownloader",
    "getDownloader",
    "isUrlSupported",
]

from .base_downloader import BaseDownloader
from .youtube_downloader import YouTubeDownloader
from .facebook_downloader import FacebookDownloader
from .instagram_downloader import InstagramDownloader
from .tiktok_downloader import TikTokDownloader
from .twitter_downloader import TwitterDownloader
from .downloader_factory import DownloaderFactory


# Convenience functions for external use
def registerDownloader(downloader: BaseDownloader) -> None:
    """
    Register a new downloader implementation.
    
    Args:
        downloader: Instance of a BaseDownloader subclass
        
    Example:
        >>> from video_downloader_pro.downloaders import registerDownloader
        >>> registerDownloader(InstagramDownloader())
    """
    DownloaderFactory.registerDownloader(downloader)


def getDownloader(url: str) -> Optional[BaseDownloader]:  # Changed: Added Optional
    """
    Get appropriate downloader for the given URL.
    
    Args:
        url: Video URL to download
        
    Returns:
        Downloader instance or None if unsupported
        
    Example:
        >>> downloader = getDownloader("https://youtube.com/watch?v=123")
        >>> if downloader:
        >>>     print(downloader.getProviderName())  # "YouTube"
    """
    return DownloaderFactory.getDownloader(url)


def isUrlSupported(url: str) -> bool:
    """
    Check if URL is supported by any registered downloader.
    
    Args:
        url: Video URL to check
        
    Returns:
        True if supported, False otherwise
    """
    return DownloaderFactory.getDownloader(url) is not None