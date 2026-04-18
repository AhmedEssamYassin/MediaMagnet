"""
Desktop notification service for download completion and error alerts.
Handles Windows NOTIFYICONDATAW API character limits and icon resolution.
"""

import os
import sys
from abc import ABC, abstractmethod

class NotificationService(ABC):
    """Abstract base class for notification services"""

    @abstractmethod
    def sendNotification(self, title: str, message: str):
        pass

class DesktopNotifier(NotificationService):
    """Desktop notification implementation"""

    def __init__(self):
        try:
            from plyer import notification
            self.notification = notification
        except ImportError:
            self.notification = None

    def _getIconPath(self):
        """Resolves the absolute path to the icon file"""
        iconName = "icon.ico"
        
        # 1. Determine base path
        if getattr(sys, 'frozen', False):
            # PyInstaller: Temp folder root
            basePath = sys._MEIPASS
        else:
            # Dev Mode: Go up 3 levels: services/ -> src/ -> Project Root
            basePath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        # 2. Check possible locations
        candidates = [
            os.path.join(basePath, "assets", "images", iconName), # Dev structure
            os.path.join(basePath, "assets", iconName),           # Flat assets structure
            os.path.join(basePath, iconName)                      # Root (rare)
        ]

        for path in candidates:
            if os.path.exists(path):
                return path
        
        return None

    """
    Desktop notifications in Windows are handled by the NOTIFYICONDATAW API structure, 
    which has extremely strict, hardcoded memory limits for strings. 
    If a program attempts to pass a string longer than these limits, the OS rejects it, 
    causing libraries like plyer to throw a ValueError and crash the thread.

    Title Limit: The notification title cannot exceed 64 characters.

    Message Limit: The notification message body cannot exceed 256 characters.
    """

    def sendNotification(self, title: str, message: str):
        if self.notification:
            try:
                safeTitle = title[:60] + "..." if len(title) > 64 else title
                safeMsg = message[:250] + "..." if len(message) > 256 else message
                # Get the icon path
                iconPath = self._getIconPath()

                kwargs = {
                    'title': safeTitle,
                    'message': safeMsg,
                    'app_name': "Video Downloader Pro",
                    'timeout': 10
                }

                if iconPath:
                    kwargs['app_icon'] = iconPath

                # Unpack arguments
                self.notification.notify(**kwargs)
            except Exception as e:
                print(f"Failed to send notification: {e}")
        else:
            print(f"INFO: Notification service not available. Please install 'plyer'.\n{title}: {message}")