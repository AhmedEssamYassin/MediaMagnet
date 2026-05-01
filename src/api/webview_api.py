import os
import json
from tkinter import filedialog
import tkinter as tk
import webview
from ..core.events import EventEmitter, EventType
from ..core.download_controller import DownloadController
from ..downloaders.downloader_factory import DownloaderFactory
from ..utils import SettingsManager, AssetLoader
from ..services.update_service import UpdateService

class WebViewApi:
    """Bridge API between Python backend and the HTML/JS frontend."""
    
    def __init__(self, controller: DownloadController):
        self._controller = controller
        self._window = None
        self._bindEvents()

    def setWindow(self, window):
        """Called by main.py immediately after creating the webview window"""
        self._window = window

    def _bindEvents(self):
        """Listen to backend events and dispatch them to the frontend via JS"""
        EventEmitter.on(EventType.DOWNLOAD_ADDED, self._dispatchEventAdded)
        EventEmitter.on(EventType.DOWNLOAD_START, self._dispatchEventStart)
        EventEmitter.on(EventType.DOWNLOAD_PROGRESS, self._dispatchEventProgress)
        EventEmitter.on(EventType.DOWNLOAD_COMPLETE, self._dispatchEventComplete)
        EventEmitter.on(EventType.DOWNLOAD_ERROR, self._dispatchEventError)
        EventEmitter.on(EventType.DOWNLOAD_CANCELLED, self._dispatchEventCancelled)

    def _safeExecuteJs(self, jsCode):
        if self._window:
            try:
                self._window.evaluate_js(jsCode)
            except Exception as e:
                print(f"Error executing JS: {e}")

    # ===== Frontend API Methods =====

    def fetchVideoInfo(self, url):
        """Fetch video metadata and return as JSON serializable dict"""
        try:
            from ..data_models import PlaylistInfo
            from ..core.download_manager import DownloadManager
            
            info = DownloadManager.getVideoInfo(url)
            self._controller.videoInfo = info
            
            isPlaylist = isinstance(info, PlaylistInfo)
            
            if isPlaylist:
                cleanEntries = []
                for entry in info.videos:
                    durationSec = int(entry.get('duration', 0) or 0)
                    mins, secs = divmod(durationSec, 60)
                    hrs, mins = divmod(mins, 60)
                    durationStr = f"{hrs:02d}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"

                    cleanEntries.append({
                        "title": entry.get("title", "Unknown"),
                        "url": entry.get("url", ""),
                        "duration": durationStr if durationSec else "N/A",
                        "thumbnail": entry.get("thumbnail", "")
                    })
                return {
                    "success": True,
                    "isPlaylist": True,
                    "title": info.title,
                    "duration": "Playlist",
                    "thumbnail": "",
                    "raw": {"entries": cleanEntries}
                }
            else:
                return {
                    "success": True,
                    "isPlaylist": False,
                    "title": getattr(info, "title", "Unknown"),
                    "duration": getattr(info, "duration", "N/A"),
                    "thumbnail": getattr(info, "thumbnail", ""),
                    "raw": None
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def startDownload(self, url, formatType, quality, outputPath):
        """Called by JS to start a single download"""
        try:
            from ..data_models import DownloadConfig
            config = DownloadConfig(url=url, outputPath=outputPath, quality=quality, formatType=formatType.upper())

            self._controller.startDownload(config)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def startPlaylistDownload(self, formatType, quality, outputPath, selectedUrls):
        """Called by JS to start a playlist download"""
        try:
            from ..data_models import DownloadConfig
            # Pass a dummy url for the config since it's a playlist. The controller will use selectedUrls.
            config = DownloadConfig(url="playlist", outputPath=outputPath, quality=quality, formatType=formatType.upper())
            self._controller.startDownload(config, selectedVideos=selectedUrls)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def getHistory(self):
        """Fetch download history"""
        try:
            historyList = self._controller.getHistory()

            cleanHistory = []
            for idx, entry in enumerate(historyList):
                cleanHistory.append({
                    "index": idx,
                    "title": entry.get("title", "Unknown"),
                    "url": entry.get("url", ""),
                    "outputPath": entry.get("path", ""),
                    "status": entry.get("status", "Unknown"),
                    "timestamp": entry.get("timestamp", None),
                    "thumbnail": entry.get("thumbnail", ""),
                })
            return {"success": True, "history": cleanHistory}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def removeHistoryEntry(self, index):
        """Remove a single entry from history by its index"""
        try:
            self._controller.removeHistoryEntry(int(index))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def clearHistory(self):
        """Clear all download history"""
        try:
            self._controller.clearHistory()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def openPath(self, path):
        """Open the specific path in native OS File Explorer"""
        try:
            import subprocess
            import platform
            
            if not os.path.exists(path):
                return {"success": False, "error": "Directory does not exist."}
                
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
                
            return {"success": True}
        except Exception as e:
            print(f"Error opening explicit path: {e}")
            return {"success": False, "error": str(e)}

    def getClipboard(self):
        """Read clipboard text via tkinter to bypass WebView2 permission prompts"""
        try:
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text
        except Exception:
            return ""

    def cancelDownload(self, jobId):
        """Called by JS to cancel a specific job"""
        try:
            self._controller.cancelJob(jobId)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def browseDirectory(self, currentDir):
        """Open native directory picker dialog"""
        # tkinter filedialog requires a hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Force dialog above the pywebview window
        root.attributes("-topmost", True)
        directory = filedialog.askdirectory(initialdir=currentDir)
        root.destroy()
        
        if directory:
            SettingsManager.setDefaultDownloadPath(directory)
            return directory
        return None

    def getSettings(self):
        """Return app settings to the frontend on load"""
        return {
            "defaultPath": SettingsManager.getDefaultDownloadPath(),
            "theme": SettingsManager.getTheme(),
            "maxConcurrent": SettingsManager.getMaxConcurrentDownloads(),
            "maxConcurrentParts": SettingsManager.getMaxConcurrentParts(),
            "language": SettingsManager.getLanguage(),
            "notifications": SettingsManager.areNotificationsEnabled(),
            "rememberPath": SettingsManager.shouldRememberLastPath(),
            "defaultFormat": SettingsManager.getDefaultFormat(),
            "defaultQuality": SettingsManager.getDefaultQuality()
        }
        
    def savePreferences(self, formatType, quality, path=None):
        """Save standard UI preferences immediately when changed interactively"""
        try:
            SettingsManager.setDefaultFormat(str(formatType))
            SettingsManager.setDefaultQuality(str(quality))
            if path:
                SettingsManager.setDefaultDownloadPath(str(path))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def saveSettings(self, maxConcurrent, maxConcurrentParts, language, notifications, rememberPath, theme=None, defaultPath=None):
        """Save settings preferences"""
        try:
            SettingsManager.setMaxConcurrentDownloads(int(maxConcurrent))
            SettingsManager.setMaxConcurrentParts(int(maxConcurrentParts))
            SettingsManager.setLanguage(str(language))
            SettingsManager.setNotificationsEnabled(bool(notifications))
            SettingsManager.setRememberLastPath(bool(rememberPath))
            if theme:
                SettingsManager.setTheme(str(theme))
            if defaultPath:
                SettingsManager.setDefaultDownloadPath(str(defaultPath))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def saveTheme(self, theme):
        """Save theme preference"""
        SettingsManager.setTheme(theme)
        return True

    def getAppVersion(self):
        """Get current application version from config"""
        try:
            config = AssetLoader.loadConfig()
            return config.get("version", "Unknown")
        except Exception:
            return "Unknown"

    def checkForUpdates(self):
        """Check for new software updates"""
        try:
            version = self.getAppVersion()
            hasUpdate, latestVersion, downloadUrl = UpdateService.checkForUpdates(version)
            return {
                "success": True,
                "hasUpdate": hasUpdate,
                "latestVersion": latestVersion,
                "downloadUrl": downloadUrl
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def performUpdate(self, downloadUrl):
        """Start the automated update process"""
        try:
            def onProgress(p):
                js = f"window.dispatchEvent(new CustomEvent('update_progress', {{detail: {{progress: {p}}}}}));"
                self._safeExecuteJs(js)

            def onComplete():
                js = "window.dispatchEvent(new CustomEvent('update_complete'));"
                self._safeExecuteJs(js)

            def onError(err):
                js = f"window.dispatchEvent(new CustomEvent('update_error', {{detail: {{error: '{err}'}}}}));"
                self._safeExecuteJs(js)

            UpdateService.downloadAndInstall(
                downloadUrl,
                progressCallback=onProgress,
                completedCallback=onComplete,
                errorCallback=onError
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ===== Private Event Dispatchers =====
    
    def _createDispatch(self, eventName, job):
        """Helper to serialize a job and send custom event to javascript window"""
        jobData = {
            "id": job.id,
            "url": getattr(job, "url", getattr(job.config, "url", "") if hasattr(job, "config") else ""),
            "title": getattr(job, "title", ""),
            "status": getattr(job.status, "value", str(job.status)) if hasattr(job, "status") else "Unknown",
            "progress": getattr(job, "progress", 0.0),
            "speed": getattr(job, "speed", ""),
            "eta": getattr(job, "eta", ""),
            "totalBytes": getattr(job, "totalBytes", 0)
        }

        jsonStr = json.dumps(jobData)
        jsCmd = f"window.dispatchEvent(new CustomEvent('{eventName}', {{detail: {jsonStr}}}));"
        self._safeExecuteJs(jsCmd)

    def _dispatchEventAdded(self, job):
        self._createDispatch("download_added", job)

    def _dispatchEventStart(self, job):
        self._createDispatch("download_start", job)

    def _dispatchEventProgress(self, job):
        self._createDispatch("download_progress", job)

    def _dispatchEventComplete(self, job):
        self._createDispatch("download_complete", job)

    def _dispatchEventError(self, job, errorMsg):
        jobData = {
            "id": getattr(job, "id", "unknown"),
            "error": str(errorMsg)
        }
        jsonStr = json.dumps(jobData)
        jsCmd = f"window.dispatchEvent(new CustomEvent('download_error', {{detail: {jsonStr}}}));"
        self._safeExecuteJs(jsCmd)

    def _dispatchEventCancelled(self, job):
        self._createDispatch("download_cancelled", job)

