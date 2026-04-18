"""
Standalone updater executable for Video Downloader Pro.
Replaces the entire app directory with a new version extracted from a .zip update.
Built separately as a --onefile PyInstaller binary so it can run independently.

Usage: updater.exe <appDir> <updateDir> <exeName>
"""

import sys
import os
import time
import shutil
import tkinter as tk
from tkinter import ttk
from threading import Thread

def performUpdate(appDir, updateDir, exeName, root, statusLabel):
    """Replace the entire app directory with the update contents"""
    
    def updateText(text):
        """Safely update UI label from background thread"""
        root.after(0, lambda: statusLabel.config(text=text))
        
    def closeUpdater():
        root.after(0, root.destroy)

    exePath = os.path.join(appDir, exeName)
    updateText(f"Waiting for {exeName} to close...")
    
    # Wait for the main process to release file locks (max 15 seconds)
    for _ in range(15):
        try:
            # Try to open the exe exclusively to confirm it's not running
            if os.path.exists(exePath):
                with open(exePath, 'ab'):
                    pass
            break
        except (PermissionError, OSError):
            time.sleep(1)
    else:
        updateText("Timeout waiting for app to close...")
        time.sleep(3)
        closeUpdater()
        return
    
    # Replace app directory contents with the update
    updateText("Installing update...")
    try:
        # Remove old files from app directory, but keep the directory itself
        for item in os.listdir(appDir):
            itemPath = os.path.join(appDir, item)
            try:
                if os.path.isdir(itemPath):
                    shutil.rmtree(itemPath)
                else:
                    os.remove(itemPath)
            except Exception:
                # Some files may be locked (e.g., logs), skip them
                pass
        
        # Copy new files from the extracted update into the app directory
        for item in os.listdir(updateDir):
            srcPath = os.path.join(updateDir, item)
            dstPath = os.path.join(appDir, item)
            if os.path.isdir(srcPath):
                shutil.copytree(srcPath, dstPath)
            else:
                shutil.copy2(srcPath, dstPath)
                
    except Exception as e:
        updateText(f"Failed to install: {e}")
        time.sleep(3)
        closeUpdater()
        return
    
    # Cleanup extracted temp directory
    try:
        # updateDir might be inside a parent temp folder, clean the parent
        parentTemp = os.path.dirname(updateDir)
        if "vdp_update" in os.path.basename(parentTemp):
            shutil.rmtree(parentTemp, ignore_errors=True)
        else:
            shutil.rmtree(updateDir, ignore_errors=True)
        # Also remove the downloaded zip if it still exists
        zipPath = os.path.join(os.path.dirname(updateDir), "vdp_update.zip")
        if os.path.exists(zipPath):
            os.remove(zipPath)
    except Exception:
        pass
    
    updateText("Starting application...")
    try:
        newExePath = os.path.join(appDir, exeName)
        os.startfile(newExePath)
    except Exception:
        pass
        
    time.sleep(1)
    closeUpdater()

def main():
    if len(sys.argv) != 4:
        print("Usage: updater.exe <appDir> <updateDir> <exeName>")
        sys.exit(1)
        
    appDir = sys.argv[1]
    updateDir = sys.argv[2]
    exeName = sys.argv[3]
    
    # Setup simple UI
    root = tk.Tk()
    root.title("Updating...")
    
    # Calculate screen center
    windowWidth = 380
    windowHeight = 130
    screenWidth = root.winfo_screenwidth()
    screenHeight = root.winfo_screenheight()
    centerX = int(screenWidth / 2 - windowWidth / 2)
    centerY = int(screenHeight / 2 - windowHeight / 2)
    
    root.geometry(f'{windowWidth}x{windowHeight}+{centerX}+{centerY}')
    root.resizable(False, False)
    root.attributes("-topmost", True)
    
    statusLabel = tk.Label(root, text="Initializing update...", font=("Segoe UI", 10))
    statusLabel.pack(pady=(20, 10))
    
    progressBar = ttk.Progressbar(root, mode='indeterminate', length=300)
    progressBar.pack(pady=10)
    progressBar.start(15)
    
    # Run update logic in a background thread so the UI doesn't freeze
    Thread(target=performUpdate, args=(appDir, updateDir, exeName, root, statusLabel), daemon=True).start()
    
    root.mainloop()

if __name__ == "__main__":
    main()