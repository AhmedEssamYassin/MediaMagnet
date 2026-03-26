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
        self._bind_events()

    def set_window(self, window):
        """Called by main.py immediately after creating the webview window"""
        self._window = window

    def _bind_events(self):
        """Listen to backend events and dispatch them to the frontend via JS"""
        EventEmitter.on(EventType.DOWNLOAD_ADDED, self._dispatch_event_added)
        EventEmitter.on(EventType.DOWNLOAD_START, self._dispatch_event_start)
        EventEmitter.on(EventType.DOWNLOAD_PROGRESS, self._dispatch_event_progress)
        EventEmitter.on(EventType.DOWNLOAD_COMPLETE, self._dispatch_event_complete)
        EventEmitter.on(EventType.DOWNLOAD_ERROR, self._dispatch_event_error)
        EventEmitter.on(EventType.DOWNLOAD_CANCELLED, self._dispatch_event_cancelled)

    def _safe_execute_js(self, js_code):
        if self._window:
            try:
                self._window.evaluate_js(js_code)
            except Exception as e:
                print(f"Error executing JS: {e}")

    # ===== Frontend API Methods =====

    def fetch_video_info(self, url):
        """Fetch video metadata and return as JSON serializable dict"""
        try:
            from ..data_models import PlaylistInfo
            from ..core.download_manager import DownloadManager
            
            info = DownloadManager.getVideoInfo(url)
            self._controller.videoInfo = info
            
            is_playlist = isinstance(info, PlaylistInfo)
            
            if is_playlist:
                clean_entries = []
                for entry in info.videos:
                    clean_entries.append({
                        'title': entry.get('title', 'Unknown'),
                        'url': entry.get('url', ''),
                        'duration': 'N/A',
                        'thumbnail': ''
                    })
                return {
                    'success': True,
                    'isPlaylist': True,
                    'title': info.title,
                    'duration': 'Playlist',
                    'thumbnail': '',
                    'raw': {'entries': clean_entries}
                }
            else:
                return {
                    'success': True,
                    'isPlaylist': False,
                    'title': getattr(info, 'title', 'Unknown'),
                    'duration': getattr(info, 'duration', 'N/A'),
                    'thumbnail': getattr(info, 'thumbnail', ''),
                    'raw': None
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def start_download(self, url, format_type, quality, output_path):
        """Called by JS to start a single download"""
        try:
            from ..data_models import DownloadConfig
            config = DownloadConfig(url=url, outputPath=output_path, quality=quality, formatType=format_type)

            self._controller.startDownload(config)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_history(self):
        """Fetch download history"""
        try:
            historyList = self._controller.getHistory()

            clean_history = []
            for idx, entry in enumerate(historyList):
                clean_history.append({
                    'index': idx,
                    'title': entry.get('title', 'Unknown'),
                    'url': entry.get('url', ''),
                    'outputPath': entry.get('path', ''),
                    'status': entry.get('status', 'Unknown'),
                    'timestamp': entry.get('timestamp', None),
                })
            return {'success': True, 'history': clean_history}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def remove_history_entry(self, index):
        """Remove a single entry from history by its index"""
        try:
            self._controller.removeHistoryEntry(int(index))
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def clear_history(self):
        """Clear all download history"""
        try:
            self._controller.clearHistory()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def open_path(self, path):
        """Open the specific path in native OS File Explorer"""
        try:
            import subprocess
            import platform
            
            if not os.path.exists(path):
                return {'success': False, 'error': 'Directory does not exist.'}
                
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
                
            return {'success': True}
        except Exception as e:
            print(f"Error opening explicit path: {e}")
            return {'success': False, 'error': str(e)}

    def start_playlist_download(self, format_type, quality, output_path, selected_urls):
        """Called by JS to start a playlist download in bulk"""
        try:
            from ..data_models import DownloadConfig

            config = DownloadConfig(url='playlist', outputPath=output_path, quality=quality, formatType=format_type)
            self._controller.startDownload(config, selectedVideos=selected_urls)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def cancel_download(self, job_id):
        """Called by JS to cancel a specific job"""
        try:
            self._controller.cancelJob(job_id)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def browse_directory(self, current_dir):
        """Open native directory picker dialog"""
        # tkinter filedialog requires a hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Force dialog above the pywebview window
        root.attributes('-topmost', True)
        directory = filedialog.askdirectory(initialdir=current_dir)
        root.destroy()
        
        if directory:
            SettingsManager.setDefaultDownloadPath(directory)
            return directory
        return None

    def get_settings(self):
        """Return app settings to the frontend on load"""
        return {
            'defaultPath': SettingsManager.getDefaultDownloadPath(),
            'theme': SettingsManager.getTheme(),
            'maxConcurrent': SettingsManager.getMaxConcurrentDownloads(),
            'maxConcurrentParts': SettingsManager.getMaxConcurrentParts(),
            'language': SettingsManager.getLanguage(),
            'notifications': SettingsManager.areNotificationsEnabled(),
            'rememberPath': SettingsManager.shouldRememberLastPath(),
            'defaultFormat': SettingsManager.getDefaultFormat(),
            'defaultQuality': SettingsManager.getDefaultQuality()
        }
        
    def save_preferences(self, format_type, quality, path=None):
        """Save standard UI preferences immediately when changed interactively"""
        try:
            SettingsManager.setDefaultFormat(str(format_type))
            SettingsManager.setDefaultQuality(str(quality))
            if path:
                SettingsManager.setDefaultDownloadPath(str(path))
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
    def save_settings(self, max_concurrent, max_concurrent_parts, language, notifications, remember_path, theme=None, default_path=None):
        """Save settings preferences"""
        try:
            SettingsManager.setMaxConcurrentDownloads(int(max_concurrent))
            SettingsManager.setMaxConcurrentParts(int(max_concurrent_parts))
            SettingsManager.setLanguage(str(language))
            SettingsManager.setNotificationsEnabled(bool(notifications))
            SettingsManager.setRememberLastPath(bool(remember_path))
            if theme:
                SettingsManager.setTheme(str(theme))
            if default_path:
                SettingsManager.setDefaultDownloadPath(str(default_path))
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def save_theme(self, theme):
        """Save theme preference"""
        SettingsManager.setTheme(theme)
        return True

    def get_app_version(self):
        """Get current application version from config"""
        try:
            config = AssetLoader.loadConfig()
            return config.get('version', 'Unknown')
        except Exception:
            return 'Unknown'

    def check_for_updates(self):
        """Check for new software updates"""
        try:
            version = self.get_app_version()
            has_update, latest_version, download_url = UpdateService.checkForUpdates(version)
            return {
                'success': True,
                'hasUpdate': has_update,
                'latestVersion': latest_version,
                'downloadUrl': download_url
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def perform_update(self, download_url):
        """Start the automated update process"""
        try:
            def on_progress(p):
                js = f"window.dispatchEvent(new CustomEvent('update_progress', {{detail: {{progress: {p}}}}}));"
                self._safe_execute_js(js)

            def on_complete():
                js = "window.dispatchEvent(new CustomEvent('update_complete'));"
                self._safe_execute_js(js)

            def on_error(err):
                js = f"window.dispatchEvent(new CustomEvent('update_error', {{detail: {{error: '{err}'}}}}));"
                self._safe_execute_js(js)

            UpdateService.downloadAndInstall(
                download_url,
                progressCallback=on_progress,
                completedCallback=on_complete,
                errorCallback=on_error
            )
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ===== Private Event Dispatchers =====
    
    def _create_dispatch(self, event_name, job):
        """Helper to serialize a job and send custom event to javascript window"""
        job_data = {
            'id': job.id,
            'url': getattr(job, 'url', getattr(job.config, 'url', '') if hasattr(job, 'config') else ''),
            'title': getattr(job, 'title', ''),
            'status': getattr(job.status, 'value', str(job.status)) if hasattr(job, 'status') else 'Unknown',
            'progress': getattr(job, 'progress', 0.0),
            'speed': getattr(job, 'speed', ''),
            'eta': getattr(job, 'eta', ''),
            'fileSize': getattr(job, 'fileSize', '')
        }
        

        json_str = json.dumps(job_data).replace("'", "\\'")
        js_cmd = f"window.dispatchEvent(new CustomEvent('{event_name}', {{detail: {json_str}}}));"
        self._safe_execute_js(js_cmd)

    def _dispatch_event_added(self, job):
        self._create_dispatch("download_added", job)

    def _dispatch_event_start(self, job):
        self._create_dispatch("download_start", job)

    def _dispatch_event_progress(self, job):
        self._create_dispatch("download_progress", job)

    def _dispatch_event_complete(self, job):
        self._create_dispatch("download_complete", job)

    def _dispatch_event_error(self, job, error_msg):
        job_data = {
            'id': getattr(job, 'id', 'unknown'),
            'error': str(error_msg)
        }
        json_str = json.dumps(job_data).replace("'", "\\'")
        js_cmd = f"window.dispatchEvent(new CustomEvent('download_error', {{detail: {json_str}}}));"
        self._safe_execute_js(js_cmd)

    def _dispatch_event_cancelled(self, job):
        self._create_dispatch("download_cancelled", job)
