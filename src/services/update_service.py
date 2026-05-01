"""
Self-update service for the application.
Downloads a .zip archive of the new version, extracts it,
and launches the updater to replace the entire app directory.
"""

import requests
import sys
import os
import subprocess
import time
import shutil
import tempfile
import zipfile
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
        newZipPath = None
        extractDir = None
        try:
            # 1. Determine safe paths based on PyInstaller state
            if not getattr(sys, 'frozen', False):
                if errorCallback: errorCallback("Cannot self-update in dev environment")
                return

            currentExePath = sys.executable
            appDir = os.path.dirname(currentExePath)
            
            # Temp paths for the downloaded zip and extraction
            newZipPath = os.path.join(tempfile.gettempdir(), "mm_update.zip")
            extractDir = os.path.join(tempfile.gettempdir(), "mm_update")
            
            # Clean up any leftover temp files from a previous failed update
            if os.path.exists(extractDir):
                shutil.rmtree(extractDir, ignore_errors=True)
            
            # Locate updater.exe in the app directory (--onedir layout)
            updaterPath = os.path.join(appDir, "updater.exe")
            if not os.path.exists(updaterPath):
                # Fallback: check _MEIPASS for legacy --onefile builds
                meipass = getattr(sys, '_MEIPASS', appDir)
                updaterPath = os.path.join(meipass, "updater.exe")
                    
            if not os.path.exists(updaterPath):
                if errorCallback: errorCallback("Updater executable not found in built assets!")
                return

            # Copy the updater to a safe location outside the app directory.
            # The updater will replace the entire app folder, so it can't run from inside it.
            safeUpdaterPath = os.path.join(tempfile.gettempdir(), "updater_run.exe")
            shutil.copy2(updaterPath, safeUpdaterPath)

            # 2. Download the .zip archive with network resilience
            response = requests.get(downloadUrl, stream=True, timeout=(10, 60))
            response.raise_for_status()
            
            totalSize = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(newZipPath, 'wb') as file:
                for data in response.iter_content(chunk_size=8192):
                    if not data:
                        break
                    file.write(data)
                    downloaded += len(data)
                    if progressCallback and totalSize > 0:
                        progressCallback(min(downloaded / totalSize, 1.0))
            
            # Verify download integrity
            if totalSize > 0 and downloaded != totalSize:
                if errorCallback: errorCallback("Download incomplete due to network drop!")
                return
            
            # 3. Extract the zip to a temp directory
            with zipfile.ZipFile(newZipPath, 'r') as zf:
                zf.extractall(extractDir)
            
            # The zip may contain a single top-level folder (e.g., "MediaMagnet/").
            # Detect this and point to the inner folder if present.
            extractedContents = os.listdir(extractDir)
            if len(extractedContents) == 1:
                innerDir = os.path.join(extractDir, extractedContents[0])
                if os.path.isdir(innerDir):
                    extractDir = innerDir
            
            # 4. Download finished successfully
            if completedCallback:
                completedCallback()
            
            # 5. Launch isolated updater and exit
            # Args: updater.exe <appDir> <updateDir> <exeName>
            exeName = os.path.basename(currentExePath)
            UpdateService._launchUpdater(safeUpdaterPath, appDir, extractDir, exeName)

        except Exception as e:
            # Cleanup any partially downloaded files
            if newZipPath and os.path.exists(newZipPath):
                try:
                    os.remove(newZipPath)
                except Exception:
                    pass
            if extractDir and os.path.exists(extractDir):
                try:
                    shutil.rmtree(extractDir, ignore_errors=True)
                except Exception:
                    pass
            if errorCallback:
                errorCallback(f"Update failed: {str(e)}")

    @staticmethod
    def _launchUpdater(updaterPath, appDir, updateDir, exeName):
        """
        Launches the updater executable detached from the current process tree.
        Args: updater.exe <appDir> <updateDir> <exeName>
        """
        try:
            subprocess.Popen(
                [updaterPath, appDir, updateDir, exeName],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
        except Exception as e:
            print(f"Failed to launch updater: {e}")
        finally:
            # Exit main app so the updater can safely replace the directory
            os._exit(0)