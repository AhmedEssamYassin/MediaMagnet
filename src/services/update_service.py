import requests
import sys
import os
import subprocess
import time
import shutil
import tempfile
from packaging import version
from threading import Thread

class UpdateService:
    VERSION_URL = "https://gist.githubusercontent.com/AhmedEssamYassin/19fe6b989b7abf1365d81829957fcac1/raw/version.json"
    
    @staticmethod
    def checkForUpdates(currentVersion):
        """Checks if a new version exists. Returns (bool, version, url)"""
        try:
            # A timeout so the app doesn't hang if the network drops
            response = requests.get(f"{UpdateService.VERSION_URL}?t={int(time.time())}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                latestVersion = data.get("latest_version")
                downloadUrl = data.get("download_url")
                
                if latestVersion and version.parse(latestVersion) > version.parse(currentVersion):
                    return True, latestVersion, downloadUrl
            return False, None, None
        except Exception:
            return False, None, None

    @staticmethod
    def downloadAndInstall(downloadUrl, progressCallback=None, completedCallback=None, errorCallback=None):
        """
        Downloads the update in a background thread to prevent UI freezing 
        and triggers the restart/install process.
        """
        # 1. Start the download in a background thread
        thread = Thread(
            target=UpdateService._downloadTask,
            args=(downloadUrl, progressCallback, completedCallback, errorCallback),
            daemon=True
        )
        thread.start()

    @staticmethod
    def _downloadTask(downloadUrl, progressCallback, completedCallback, errorCallback):
        newExePath = None
        try:
            # 1. Determine safe paths based on PyInstaller state
            if not getattr(sys, 'frozen', False):
                if errorCallback: errorCallback("Cannot self-update in dev environment")
                return

            currentExePath = sys.executable
            currentDir = os.path.dirname(currentExePath)
            newExePath = currentExePath + ".new"
            
            # Locate updater.exe correctly whether it's a --onefile or --onedir build
            meipass = getattr(sys, '_MEIPASS', currentDir)
            possiblePaths = [
                os.path.join(meipass, "updater.exe"),   # Location for --onefile build
                os.path.join(currentDir, "updater.exe") # Location for --onedir build
            ]
            
            updaterPath = None
            for path in possiblePaths:
                if os.path.exists(path):
                    updaterPath = path
                    break
                    
            if not updaterPath:
                if errorCallback: errorCallback("Updater executable not found in built assets!")
                return

            # Copy the updater out of the PyInstaller temp directory.
            # PyInstaller deletes _MEIPASS when the main app closes. Running it from there
            # will cause lock conflicts. Moving it to the OS temp folder guarantees safe execution.
            safeUpdaterPath = os.path.join(tempfile.gettempdir(), "updater_run.exe")
            shutil.copy2(updaterPath, safeUpdaterPath)

            # 2. Download the file with network resilience
            response = requests.get(downloadUrl, stream=True, timeout=(10, 30))
            response.raise_for_status() # Catches 404s and 500s immediately
            
            totalSize = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(newExePath, 'wb') as file:
                # Increased chunk size to 8192 for slightly faster disk writing
                for data in response.iter_content(chunk_size=8192):
                    if not data:
                        break
                    file.write(data)
                    downloaded += len(data)
                    if progressCallback and totalSize > 0:
                        # Cap progress at 1.0 (100%)
                        progressCallback(min(downloaded / totalSize, 1.0))
            
            # Verify the integrity of the downloaded file
            if totalSize > 0 and downloaded != totalSize:
                if os.path.exists(newExePath):
                    os.remove(newExePath)
                if errorCallback: errorCallback("Download incomplete due to network drop!")
                return
            
            # 3. Download finished successfully
            if completedCallback:
                completedCallback()
            
            # 4. Launch isolated updater and exit
            UpdateService._launchUpdater(safeUpdaterPath, currentExePath, newExePath)

        except Exception as e:
            # Cleanup any partially downloaded ghost files
            if newExePath and os.path.exists(newExePath):
                try:
                    os.remove(newExePath)
                except Exception:
                    pass
            if errorCallback:
                errorCallback(f"Update failed: {str(e)}")

    @staticmethod
    def _launchUpdater(updaterPath, oldExe, newExe):
        """
        Launches the updater executable detached from the current process tree.
        """
        try:
            subprocess.Popen(
                [updaterPath, oldExe, newExe],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
        except Exception as e:
            print(f"Failed to launch updater: {e}")
        finally:
            # Exit main app so the updater can safely overwrite the .exe
            os._exit(0)