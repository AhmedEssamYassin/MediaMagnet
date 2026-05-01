"""
Settings manager for user preferences and configuration persistence
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

class SettingsManager:
    """Manage user settings and preferences"""
    
    # User settings file location
    if __import__('os').name == 'nt':  # Windows
        SETTINGS_DIR = Path.home() / "AppData" / "Local" / "MediaMagnet"
    else:  # macOS/Linux
        SETTINGS_DIR = Path.home() / ".config" / "MediaMagnet"
    
    SETTINGS_FILE = SETTINGS_DIR / "user_settings.json"
    
    # Default settings (loaded from assets/data/default_config.json)
    _defaultSettings = None
    
    @classmethod
    def _ensureSettingsDir(cls):
        """Ensure settings directory exists"""
        cls.SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def _loadDefaultSettings(cls) -> Dict[str, Any]:
        """Load default settings from assets"""
        if cls._defaultSettings is None:
            from .asset_loader import AssetLoader
            config = AssetLoader.loadConfig()
            cls._defaultSettings = config.get('settings', {})
        return cls._defaultSettings.copy()
    
    @classmethod
    def loadSettings(cls) -> Dict[str, Any]:
        """
        Load user settings from file, merge with defaults
        Returns merged settings dictionary
        """
        # Start with defaults
        settings = cls._loadDefaultSettings()
        
        # Load user overrides if they exist
        if cls.SETTINGS_FILE.exists():
            try:
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    userSettings = json.load(f)
                    # Merge user settings over defaults
                    settings.update(userSettings)
            except Exception as e:
                print(f"Error loading user settings: {e}")
                # Return defaults on error
        
        return settings
    
    @classmethod
    def saveSettings(cls, settings: Dict[str, Any]) -> bool:
        """
        Save user settings to file
        Returns True on success, False on failure
        """
        try:
            cls._ensureSettingsDir()
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    @classmethod
    def getSetting(cls, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        settings = cls.loadSettings()
        return settings.get(key, default)
    
    @classmethod
    def setSetting(cls, key: str, value: Any) -> bool:
        """Set a specific setting value and save"""
        settings = cls.loadSettings()
        settings[key] = value
        return cls.saveSettings(settings)
    
    @classmethod
    def resetToDefaults(cls) -> bool:
        """Reset all settings to defaults"""
        defaults = cls._loadDefaultSettings()
        return cls.saveSettings(defaults)
    
    @classmethod
    def getLanguage(cls) -> str:
        """Get current language setting"""
        return cls.getSetting('language', 'en')
    
    @classmethod
    def setLanguage(cls, language: str) -> bool:
        """Set language preference"""
        return cls.setSetting('language', language)
    
    @classmethod
    def getDefaultDownloadPath(cls) -> str:
        """Get default download path"""
        default = str(Path.home() / "Downloads")
        return cls.getSetting('default_download_path', default)
    
    @classmethod
    def setDefaultDownloadPath(cls, path: str) -> bool:
        """Set default download path"""
        return cls.setSetting('default_download_path', path)
    
    @classmethod
    def getDefaultQuality(cls) -> str:
        """Get default video quality"""
        return cls.getSetting('default_quality', 'best')
    
    @classmethod
    def setDefaultQuality(cls, quality: str) -> bool:
        """Set default video quality"""
        return cls.setSetting('default_quality', quality)
    
    @classmethod
    def getDefaultFormat(cls) -> str:
        """Get default output format"""
        return cls.getSetting('default_format', 'MP4')
    
    @classmethod
    def setDefaultFormat(cls, formatType: str) -> bool:
        """Set default output format"""
        return cls.setSetting('default_format', formatType)
    
    @classmethod
    def areNotificationsEnabled(cls) -> bool:
        """Check if desktop notifications are enabled"""
        return cls.getSetting('notifications_enabled', True)
    
    @classmethod
    def setNotificationsEnabled(cls, enabled: bool) -> bool:
        """Enable or disable desktop notifications"""
        return cls.setSetting('notifications_enabled', enabled)
    
    @classmethod
    def shouldRememberLastPath(cls) -> bool:
        """Check if app should remember last download path"""
        return cls.getSetting('remember_last_path', True)
    
    @classmethod
    def setRememberLastPath(cls, remember: bool) -> bool:
        """Set whether to remember last download path"""
        return cls.setSetting('remember_last_path', remember)
    
    @classmethod
    def getTheme(cls) -> str:
        """Get current theme"""
        return cls.getSetting('theme', 'dark')
    
    @classmethod
    def setTheme(cls, theme: str) -> bool:
        """Set theme (dark/light)"""
        return cls.setSetting('theme', theme)
    
    @classmethod
    def getMaxConcurrentDownloads(cls) -> int:
        """Get max concurrent downloads limit"""
        return int(cls.getSetting('max_concurrent_downloads', 3))
    
    @classmethod
    def setMaxConcurrentDownloads(cls, count: int) -> bool:
        """Set max concurrent downloads limit"""
        return cls.setSetting('max_concurrent_downloads', max(1, min(10, int(count))))
    
    @classmethod
    def getMaxConcurrentParts(cls) -> int:
        """Get maximum concurrent connection slices per video"""
        return int(cls.getSetting('max_concurrent_parts', 8))
        
    @classmethod
    def setMaxConcurrentParts(cls, count: int) -> bool:
        """Set maximum concurrent parts (1-16)"""
        return cls.setSetting('max_concurrent_parts', max(1, min(16, int(count))))
    
    @classmethod
    def exportSettings(cls, filePath: str) -> bool:
        """Export settings to a file"""
        try:
            settings = cls.loadSettings()
            with open(filePath, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False
    
    @classmethod
    def importSettings(cls, filePath: str) -> bool:
        """Import settings from a file"""
        try:
            with open(filePath, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return cls.saveSettings(settings)
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False
