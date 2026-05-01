"""
MediaMagnet - Main Entry Point

Modern Multi-Platform Media Downloader with Fancy GUI
Supports: YouTube, Facebook, Instagram, TikTok (extensible to more platforms)
"""

import sys
import os

def resourcePath(relativePath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")

    return os.path.join(basePath, relativePath)

def setupGlobalFfmpeg():
    ffmpegExe = "ffmpeg.exe"
    ffmpegPath = None

    if getattr(sys, "frozen", False):
        # Check ROOT of _MEIPASS (if added via --add-binary)
        path1 = os.path.join(sys._MEIPASS, ffmpegExe)
        # Check ASSETS folder inside _MEIPASS (if added via --add-data)
        path2 = os.path.join(sys._MEIPASS, "assets", ffmpegExe)

        if os.path.exists(path1):
            ffmpegPath = sys._MEIPASS
        elif os.path.exists(path2):
            ffmpegPath = os.path.dirname(path2)
    else:
        # Development mode
        possiblePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", ffmpegExe)
        if os.path.exists(possiblePath):
            ffmpegPath = os.path.dirname(possiblePath)

    if ffmpegPath:
        os.environ["PATH"] += os.pathsep + ffmpegPath

import webview
from src.core.download_controller import DownloadController
from src.api.webview_api import WebViewApi
from src.utils import SettingsManager  

def main():
    """Application entry point"""
    try:
        savedTheme = SettingsManager.getTheme()  
    except Exception as e:
        print(f"Failed to load theme: {e}")
        savedTheme = "dark"

    controller = DownloadController()
    api = WebViewApi(controller)

    htmlPath = resourcePath("src/web/index.html")

    window = webview.create_window(
        title="MediaMagnet",
        url=htmlPath,
        js_api=api,
        width=1000,
        height=750,
        min_size=(800, 600),
        background_color="#141726" if savedTheme == "dark" else "#fafafa"
    )
    
    api.setWindow(window)
    
    # Start the webview application (blocking call)
    webview.start(debug=False)


if __name__ == "__main__":
    setupGlobalFfmpeg()
    main()