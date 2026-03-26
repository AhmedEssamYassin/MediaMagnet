import PyInstaller.__main__
import os
import shutil
import json
import sys
import subprocess
from pathlib import Path
import update_deps

try:
    import webview
    import yt_dlp
    from yt_dlp.extractor import extractors
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}")
    print("Please install: pip install pywebview yt-dlp")
    sys.exit(1)

update_deps.updateAllDeps()    

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
ASSETS_DIR = PROJECT_ROOT / "assets"
UPDATER_PATH = PROJECT_ROOT / "updater.exe"

def getProjectVersion():
    try:
        configPath = PROJECT_ROOT / "assets" / "data" / "default_config.json"
        with open(configPath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("version", "2.0.0")
    except Exception:
        return "2.0.0"

# --- Project Configuration ---
APP_NAME = "VideoDownloaderPro"
VERSION_NUMBER = getProjectVersion()
AUTHOR_NAME = "Ahmed Yassin"
APP_DESCRIPTION = "Professional Video Downloader"


# --- Helper Functions ---

def getYtDlpExtractors():
    """Dynamically find yt-dlp extractors to avoid missing module errors"""
    try:
        from yt_dlp.extractor.extractors import _ALL_CLASSES
        extractorNames = [f"yt_dlp.extractor.{ie.IE_NAME}" for ie in _ALL_CLASSES if hasattr(ie, 'IE_NAME')]
        return extractorNames
    except Exception:
        return ['yt_dlp.extractor', 'yt_dlp.extractor.common', 'yt_dlp.extractor.generic']

def getPlyerHooks():
    """Check for plyer windows notification support"""
    try:
        import plyer.platforms.win.notification
        return ['plyer.platforms.win.notification']
    except ImportError:
        return []

def cleanBuildDirs():
    """Clean previous build directories"""
    print("Cleaning previous builds...")
    for directory in [DIST_DIR, BUILD_DIR]:
        if directory.exists():
            shutil.rmtree(directory)
    # Clean spec file
    for specFile in PROJECT_ROOT.glob("*.spec"):
        if specFile.is_file():
            specFile.unlink() # Deletes the file
            print(f"Deleted spec file: {specFile.name}")

    print("Build directories cleaned")

def ensureUpdaterExists():
    """Check if updater.exe exists, warn if not"""
    if not UPDATER_PATH.exists():
        print("\n" + "=" * 60)
        print("WARNING: updater.exe not found!")
        print(f"Expected location: {UPDATER_PATH}")
        print("Auto-update feature will not work without it.")
        print("Build updater.exe first using: pyinstaller --onefile --console --name updater updater.py")
        print("=" * 60 + "\n")
        return False
    else:
        print(f"✓ Found updater.exe: {UPDATER_PATH}")
        return True

def buildUpdater():
    print("\n" + "=" * 60)
    print("1/2: Building updater.exe...")
    print("=" * 60)
    
    updaterArgs = [
        sys.executable, '-m', 'PyInstaller',
        'updater.py',
        '--onefile',
        '--windowed',
        '--icon=assets/images/icon.ico',
        '--name', 'updater',
        '--noconfirm',
        '--clean',
        f'--distpath={PROJECT_ROOT}',
        f'--workpath={BUILD_DIR / "updaterBuild"}'
    ]
    
    try:
        subprocess.run(updaterArgs, check=True)
        if UPDATER_PATH.exists():
            print(f"Successfully built updater at: {UPDATER_PATH}")
            return True
        print("Updater build finished but updater.exe not found")
        return False
    except subprocess.CalledProcessError as err:
        print(f"Failed to build updater: {err}")
        return False
        
# --- Build Logic ---

def createSpecFile():
    """Create PyInstaller spec file with dynamic yt-dlp hooks"""
    ytHooks = getYtDlpExtractors()
    plyerHooks = getPlyerHooks()
    
    hiddenImports = [
        'webview',
        'webview.platforms.winforms',
        'clr',
        'yt_dlp',
        'requests',
        'packaging',
        'certifi',   
        'brotli',    
        'mutagen',
    ] + ytHooks + plyerHooks

    datas = [
        ('assets', 'assets'),
        ('src/web', 'src/web'),
    ]

    if UPDATER_PATH.exists():
        datas.append((str(UPDATER_PATH), '.'))
        print("✓ Bundling updater.exe")

    specContent = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('src/web', 'src/web'),
    ],
    hiddenimports={hiddenImports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/images/icon.ico' if os.path.exists('assets/images/icon.ico') else None,
)
'''
    specFile = PROJECT_ROOT / f"{APP_NAME}.spec"
    with open(specFile, 'w', encoding='utf-8') as f:
        f.write(specContent)
    
    print(f"Created spec file: {specFile}")
    return specFile

def getBaseArgs():
    """Common arguments for OneFile and OneDir"""
    ytHooks = getYtDlpExtractors()
    plyerHooks = getPlyerHooks()
    
    args = [
        'main.py',
        '--name', APP_NAME,
        '--windowed',
        '--clean',
        '--noconfirm',
        f'--distpath={DIST_DIR}',
        f'--workpath={BUILD_DIR}',
        '--add-data', f'assets{os.pathsep}assets',
        '--add-data', f'src/web{os.pathsep}src/web',
        '--collect-all', 'yt_dlp',
        '--collect-all', 'webview',
        '--hidden-import', 'requests',
        '--hidden-import', 'packaging',
        '--hidden-import', 'certifi',  
        '--hidden-import', 'brotli',   
        '--hidden-import', 'mutagen',  
    ]

    for hook in (ytHooks + plyerHooks):
        args.extend(['--hidden-import', hook])

    if UPDATER_PATH.exists():
        args.extend(['--add-data', f'{UPDATER_PATH}{os.pathsep}.'])
        print("✓ Bundling updater.exe with main app")

    ffmpegPath = ASSETS_DIR / "ffmpeg.exe"
    if ffmpegPath.exists():
        print(f"Bundling FFmpeg from: {ffmpegPath}")
        # Syntax is "source;dest" (Windows)
        args.append(f'--add-binary={ffmpegPath};.') 
    else:
        print("WARNING: FFmpeg not found in assets. High-quality merges won't work.")

    iconPath = ASSETS_DIR / "images" / "icon.ico"
    if iconPath.exists():
        args.extend(['--icon', str(iconPath)])
    
    return args

def buildOnefile():
    """Build as single file executable"""
    print("\n" + "=" * 60)
    print(f"2/2: Building {APP_NAME} (One File) v{VERSION_NUMBER}...")
    print("=" * 60)
    buildArgs = getBaseArgs()
    buildArgs.append('--onefile')
    # PyInstaller uses UPX by default if found in PATH, so no extra arg needed here
    PyInstaller.__main__.run(buildArgs)
    print(f"\nBuild complete! Location: {DIST_DIR / f'{APP_NAME}.exe'}")

def buildOnedir():
    """Build as directory with executable and dependencies"""
    print("\n" + "=" * 60)
    print(f"2/2: Building {APP_NAME} (One Directory) v{VERSION_NUMBER}...")
    print("=" * 60)
    buildArgs = getBaseArgs()
    buildArgs.append('--onedir')
    PyInstaller.__main__.run(buildArgs)

    if UPDATER_PATH.exists():
        destUpdater = DIST_DIR / APP_NAME / "updater.exe"
        shutil.copy2(UPDATER_PATH, destUpdater)
        print(f"✓ Copied updater.exe to: {destUpdater}")

    print(f"\nBuild complete! Location: {DIST_DIR / APP_NAME}")

# --- User Interface ---

def showMenu():
    """Show build options menu"""
    print("=" * 60)
    print(f"   {APP_NAME} v{VERSION_NUMBER} - Build Script")
    print("=" * 60)
    print("\nBuild Options:")
    print("   1. One File (single .exe, slower startup)")
    print("   2. One Directory (folder with .exe, faster startup)")
    print("   3. Custom spec file (uses specific yt-dlp hooks & UPX)")
    print("   4. Clean build directories only")
    print("   0. Exit")
    print()
    return input("Select option [1-4, 0]: ").strip()

def main():
    """Main build process"""
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    try:
        while(True):
            userChoice = showMenu()
            
            if userChoice == "0":
                sys.exit(0)
            
            if userChoice == "4":
                cleanBuildDirs()
                continue

            if userChoice in ["1", "2", "3"]:
                cleanBuildDirs()
                if not ASSETS_DIR.exists():
                    print(f"Warning: {ASSETS_DIR} not found. Creating empty folder.")
                    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

                buildUpdater()

                if userChoice == "1":
                    buildOnefile()
                elif userChoice == "2":
                    buildOnedir()
                elif userChoice == "3":
                    specFile = createSpecFile()
                    PyInstaller.__main__.run([str(specFile), '--clean', '--noconfirm'])

                print("\n" + "=" * 60)
                print("Build process completed successfully!")
                print("=" * 60)
                break
            else:
                print("Invalid option")
            
    except KeyboardInterrupt:
        print("\n[EXIT] Build cancelled by user.")
        sys.exit(0)
    except Exception as buildError:
        print(f"\nBuild failed: {buildError}")
        sys.exit(1)

if __name__ == "__main__":
    main()