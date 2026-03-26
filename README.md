# Video Downloader Pro — Modular Architecture with SOLID Principles & Design Patterns

> A robust, unified desktop application for downloading media from major platforms (YouTube, Facebook, Instagram, TikTok, X) while serving as a practical reference implementation of SOLID principles and Design Patterns in Python. Built on a modern **PyWebView + HTML/CSS/JS** frontend with an event-driven Python backend, Video Downloader Pro features live download telemetry, concurrent fragment acceleration, persistent settings, and a fully functional download history — all wrapped in a sleek multi-themed interface.

## Key Features

### Platform Support
- **YouTube** — Videos, playlists, quality selection
- **Facebook** — Public videos and posts
- **Instagram** — Reels, posts, stories
- **TikTok** — Videos and audio from photo posts
- **Twitter/X** — Video tweets

### Download Options
- **Video Formats** — MP4 with quality selection (best, 1080p, 720p, 480p, 360p)
- **Audio Extraction** — MP3 format with 192kbps quality
- **Custom Naming** — Edit video title before downloading
- **Flexible Output** — Choose download location with quick folder access
- **Concurrent Fragment Downloads** — Multi-part connection slicing (1–16 parts per video) for significantly faster downloads on supported streams

### User Experience
- **Modern Dark/Light Theme** — Toggle between eye-friendly themes with smooth transitions
- **Live Telemetry** — Real-time download speed (MB/s, KB/s) and ETA countdown on every active download card
- **Progress Tracking** — Visual progress bars with percentage indicators
- **Download History** — View, delete individual entries, and re-download from history
- **Graceful Cancellation** — Cancel downloads cleanly without false error notifications
- **Desktop Notifications** — Get notified when downloads complete or fail
- **Auto-Updater** — Seamless background version checking and self-updating executable replacement
- **URL Detection** — Automatic platform detection and validation
- **Persistent Settings** — All preferences (theme, paths, concurrency, language) saved across sessions
- **Skeleton Loading** — Premium loading experience instead of blank screens on startup

### Technical Highlights
- **Event-Driven Architecture** — Decoupled backend-to-frontend communication via `EventEmitter`
- **PyWebView Bridge** — Native Python ↔ JavaScript API bridge for seamless cross-layer calls
- **Asynchronous Downloads** — `ThreadPoolExecutor`-based non-blocking concurrent downloads
- **Modular Architecture** — SOLID principles with Strategy + Factory patterns
- **Extensible** — Add new platforms without modifying existing code (Open/Closed Principle)
- **Smart String Sanitization** — Strips bidirectional text, emojis, and invalid characters for Windows file-system compatibility
- **Windows API Safeguards** — Defensive truncation for desktop notifications to prevent `NOTIFYICONDATAW` character limit crashes

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5 / CSS3 / JavaScript | UI rendering, animations, dark/light themes |
| **UI Runtime** | [PyWebView](https://pywebview.flowrl.com/) | Native window with embedded web engine |
| **Backend** | Python 3.12+ | Business logic, download orchestration |
| **Download Engine** | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Multi-platform video extraction & download |
| **Media Processing** | [FFmpeg](https://ffmpeg.org/) | Audio extraction, video/audio stream merging |
| **Notifications** | [plyer](https://github.com/kivy/plyer) | Cross-platform desktop notifications |
| **Packaging** | [PyInstaller](https://pyinstaller.org/) | Single-file `.exe` distribution |
| **CI/CD** | GitHub Actions | Automated build, artifact upload, and release creation |

---

## Architecture Overview

### System Design (UML Diagram)
![UML Diagram](./docs/system%20design%20UML.svg)

### Separation of Concerns + SOLID Principles

1. **Presentation Layer** (`src/web/` + `src/api/`)
   - `index.html` — Main application layout, modals (settings, history, playlist)
   - `css/style.css` — Design system with CSS variables, dark/light theme tokens
   - `js/main.js` — Frontend logic, event listeners, dynamic card rendering
   - `webview_api.py` — Python ↔ JS bridge exposing backend methods to the frontend
   - **No business logic** — Pure presentation and API routing

2. **Business Logic Layer** (`src/core/`)
   - `download_controller.py` — Orchestrates downloads, manages job state, parses telemetry
   - `download_job.py` — Job data model with status, progress, speed, ETA tracking
   - `download_manager.py` — Facade delegating to the correct platform downloader
   - `events.py` — `EventEmitter` + `EventType` enum for decoupled communication
   - **Separation** — No UI code, no direct platform logic

3. **Service Layer** (`src/services/`)
   - `history_service.py` — Persistent download history (JSON file storage)
   - `notification_service.py` — Desktop notifications via plyer
   - `update_service.py` — Thread-safe self-updating with PyInstaller environment cleanup
   - **Abstraction** — Platform-independent services

4. **Download Strategy Layer** (`src/downloaders/`) — **OCP Implementation** ⭐
   - `base_downloader.py` — Abstract contract defining the downloader interface
   - Platform implementations — Each platform in an isolated file
   - `downloader_factory.py` — Automatic platform detection and selection
   - **Key Benefit** — Add platforms without modifying existing code

5. **Utilities & Configuration** (`src/utils/`)
   - `settings_manager.py` — Persistent user preferences (theme, paths, concurrency, language)
   - `asset_loader.py` — Configuration and translation loading
   - `file_utils.py` — FFmpeg path resolution, filename sanitization

6. **Data Layer** (`src/data_models/`)
   - `models.py` — Data structures with validation
     - `VideoInfo` — Video metadata (title, duration, thumbnail, formats)
     - `PlaylistInfo` — Playlist information with video list
     - `DownloadConfig` — Configuration with path/quality/format validation

### Data Flow Diagram
```
User Input (URL)
    ↓
Frontend (HTML/CSS/JS) ──── PyWebView Bridge ──── WebViewApi
    ↓
DownloadController (Business Logic + EventEmitter)
    ↓
DownloadManager (Facade)
    ↓
DownloaderFactory (Factory Pattern)
    ↓
Platform Downloader (Strategy Pattern)
    ↓
yt-dlp (External Library) ──── FFmpeg (Stream Merging)
    ↓
Downloaded File + History Entry + Desktop Notification
```

---

## SOLID Principles Applied

### S — Single Responsibility Principle
Each module has one clear purpose:
- Frontend only handles presentation and user interaction
- Controller only manages business logic and job state
- Each downloader only handles one platform

### O — Open/Closed Principle ⭐
**Open for extension, closed for modification:**
```python
# Adding a new platform (e.g., Reddit)
class RedditDownloader(BaseDownloader):
    def canHandle(self, url): 
        return "reddit.com" in url
    # Implement required methods
    
# Register it — NO OTHER CODE CHANGES NEEDED!
DownloaderFactory.registerDownloader(RedditDownloader())
```

### L — Liskov Substitution Principle
Any `BaseDownloader` implementation can be substituted for another without breaking the application

### I — Interface Segregation Principle
Clean, minimal abstract interface in `BaseDownloader` with only necessary methods

### D — Dependency Inversion Principle
High-level modules (WebViewApi, Controller) depend on abstractions (DownloadManager interface), not concrete implementations

---

## Open/Closed Principle Deep Dive

### The Problem It Solves

**Without OCP:**
```python
# BAD: Every new platform requires modifying existing code
def downloadVideo(url, ...):
    if "youtube.com" in url:
        # YouTube logic
    elif "facebook.com" in url:
        # Facebook logic
    elif "instagram.com" in url:  # Modification!
        # Instagram logic
    # Growing if/else chain = high risk of bugs
```

**With OCP:**
```python
# GOOD: Just add a new class, zero modifications
class TikTokDownloader(BaseDownloader):
    def canHandle(self, url):
        return "tiktok.com" in url
    # Implement interface
    
# Register and done!
DownloaderFactory.registerDownloader(TikTokDownloader())
```

### Architecture Flow

```
User enters URL → DownloadManager → Factory selects downloader
                                         ↓
                    ┌────────────────────┴────────────────────┐
                    ↓                    ↓                     ↓
            YouTubeDownloader    FacebookDownloader    [Other Downloaders]
                    
Each downloader inherits from BaseDownloader (abstract)
```

### Benefits

1. **Zero Risk** — Adding platforms can't break existing ones
2. **Parallel Development** — Different developers work on different platforms
3. **Easy Testing** — Test each platform independently
4. **No Code Duplication** — Shared interface via base class
5. **Plugin Architecture** — Platform implementations are like plugins

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/AhmedEssamYassin/Video-Downloader-Pro.git
cd Video-Downloader-Pro
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```

---

## 🔧 Module Dependencies

```
main.py (Application Entry Point)
├── pywebview (Native Window)
├── src.api.webview_api.py (Python ↔ JS Bridge)
│   ├── src.core.download_controller.py (Business Logic Orchestrator)
│   │   ├── src.core.download_manager.py (Facade)
│   │   │   └── src.downloaders.downloader_factory.py (Factory Pattern)
│   │   │       ├── src.downloaders.base_downloader.py (Abstract Interface)
│   │   │       │   └── src.data_models.models.py
│   │   │       ├── src.downloaders.youtube_downloader.py (Strategy)
│   │   │       ├── src.downloaders.facebook_downloader.py (Strategy)
│   │   │       ├── src.downloaders.instagram_downloader.py (Strategy)
│   │   │       ├── src.downloaders.tiktok_downloader.py (Strategy)
│   │   │       └── src.downloaders.twitter_downloader.py (Strategy)
│   │   ├── src.core.download_job.py (Job State Model)
│   │   ├── src.core.events.py (EventEmitter + EventType)
│   │   ├── src.services.history_service.py
│   │   ├── src.services.notification_service.py
│   │   └── src.utils.file_utils.py (Sanitization)
│   └── src.utils.settings_manager.py (Persistent Preferences)
│       └── src.utils.asset_loader.py
└── src.web/ (Frontend)
    ├── index.html (Layout + Modals)
    ├── css/style.css (Design System)
    └── js/main.js (UI Logic + Event Handlers)
```

---

## 🎯 Benefits of This Architecture

### Scalability via Open/Closed Principle
- **Easy to add platforms** — Create one new file, no modifications needed
- **Independent modules** — Changes in one platform don't affect others
- **Testing friendly** — Each platform can be tested independently
- **Plugin-like architecture** — Platforms are self-contained implementations

### Maintainability
- **Clear responsibilities** — Each module has a single, well-defined purpose
- **Easy to debug** — Issues can be isolated to specific modules/platforms
- **Code reusability** — Components and base classes are reused across layers
- **No regression risk** — Adding features can't break existing platforms

### Extensibility
- **Platform support** — YouTube, Facebook, Instagram, TikTok, Twitter — and more via OCP
- **Theme switching** — Dark/Light toggle with CSS variables
- **Format support** — Easy to add new output formats (WebM, AVI, etc.)
- **Settings expansion** — Add new preferences without refactoring

---

## Adding a New Platform (Template)

```python
# new_platform_downloader.py
from .base_downloader import BaseDownloader
from ..data_models import VideoInfo
from ..utils.settings_manager import SettingsManager
import yt_dlp
import re

class NewPlatformDownloader(BaseDownloader):
    """Downloader for NewPlatform videos"""
    
    def canHandle(self, url: str) -> bool:
        """Check if URL is from NewPlatform"""
        patterns = [
            r'newplatform\.com/',
            r'nplat\.tv/'
        ]
        return any(re.search(pattern, url) for pattern in patterns)
    
    def getVideoInfo(self, url: str) -> VideoInfo:
        """Fetch video information"""
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return VideoInfo(
                title=info.get('title', 'NewPlatform Video'),
                duration=str(info.get('duration', 0)) + 's',
                thumbnail=info.get('thumbnail', ''),
                formats=['best', '1080p', '720p', '480p']
            )
    
    def downloadVideo(self, url, outputPath, quality, 
                      formatType, progressCallback, title=None):
        """Download video with concurrent fragment support"""
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{outputPath}/%(title)s.%(ext)s',
            'progress_hooks': [progressCallback],
            'concurrent_fragment_downloads': SettingsManager.getMaxConcurrentParts(),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    
    def getProviderName(self) -> str:
        return "NewPlatform"

# Register in downloader_factory.py:
# DownloaderFactory.registerDownloader(NewPlatformDownloader())
```

That's it! One file = one new platform support!

---

## Deployment

### Local Build
```bash
python build.py
```
Select option `1` for a single `.exe` file or option `2` for a directory build.

### CI/CD (GitHub Actions)
The project includes a fully automated build pipeline (`.github/workflows/build.yml`):
- **Trigger** — Push a version tag (`v*`) or manual dispatch
- **Process** — Installs dependencies, downloads FFmpeg, runs `build.py` in non-interactive mode
- **Output** — Uploads `VideoDownloaderPro.exe` as a build artifact and creates a GitHub Release

```bash
# To trigger a release build:
git tag v2.1.0
git push origin v2.1.0
```

---

## 🔧 Troubleshooting

### Common Issues

**"Failed to fetch video info"**
- Check if the URL is publicly accessible
- Verify your internet connection
- Some platforms may block automated downloads

**"FFmpeg not found" error**
- Place `ffmpeg.exe` in the `assets/` folder
- Or install FFmpeg system-wide and add to PATH: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

**"Download failed" for Instagram/TikTok**
- These platforms frequently change their API
- Update yt-dlp: `pip install --upgrade yt-dlp`

**Slow download speeds**
- Increase **Max Concurrent Parts** in Settings (up to 16) for multi-fragment acceleration
- Some platforms throttle download speeds regardless of settings
- Try different quality settings

**Desktop notifications not working**
- Notifications require `plyer`: `pip install plyer`
- On Linux, ensure `notification-daemon` is installed

---

## 📊 Module Complexity Comparison

### Before OCP (Monolithic)
| Component | Lines | Complexity | Extensibility |
|-----------|-------|------------|---------------|
| download_manager.py | ~150 | High | ❌ Hard to extend |
| **Total** | **~150** | **High** | **Requires modification** |

### After OCP (Modular — Current Architecture)
| Module | Lines | Complexity | Purpose |
|--------|-------|------------|---------|
| base_downloader.py | ~70 | Low | Abstract contract |
| youtube_downloader.py | ~135 | Medium | YouTube logic |
| facebook_downloader.py | ~112 | Medium | Facebook logic |
| instagram_downloader.py | ~105 | Medium | Instagram logic |
| tiktok_downloader.py | ~155 | Medium | TikTok logic |
| twitter_downloader.py | ~125 | Medium | Twitter/X logic |
| downloader_factory.py | ~70 | Low | Provider selection |
| download_manager.py | ~90 | Low | Facade |
| **Total** | **~862** | **Low per file** | **✅ Just add files** |

### Scalability Analysis

**Adding a new platform (e.g., Reddit):**
- Monolithic: Modify 3–4 existing files, risk breaking 5 platforms
- OCP: Create 1 new file (~100 lines), register in factory (1 line)

**Bug in TikTok downloader:**
- Monolithic: Risk affecting all platforms in same file
- OCP: Fix isolated to `tiktok_downloader.py` only

**Team of 5 developers:**
- Monolithic: Constant merge conflicts, blocking each other
- OCP: Each developer owns a platform, parallel work with zero conflicts

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

### Third-Party Libraries

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — Video download engine
- [PyWebView](https://pywebview.flowrl.com/) — Native desktop window with embedded web engine
- [plyer](https://github.com/kivy/plyer) — Cross-platform desktop notifications
- [Pillow](https://python-pillow.org/) - Image processing
- [PyInstaller](https://pyinstaller.org/) — Executable packaging
- [FFmpeg](https://ffmpeg.org/) — Audio/video stream processing

### Disclaimer

This tool is for personal use only. Please respect copyright laws and platform terms of service. The developers are not responsible for misuse of this software.