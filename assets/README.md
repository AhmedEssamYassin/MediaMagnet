# Assets Directory

This directory contains all static assets used by MediaMagnet.

## Directory Structure
```
assets/
├── images/              # Application icons and graphics
│   ├── icon.ico        # Windows application icon (256x256, 128x128, 64x64, 32x32, 16x16)
│   └── icon.png        # PNG icon for cross-platform use
│
├── data/               # Configuration and data files
│   ├── default_config.json      # Default application settings
│   └── translations/            # Language files for internationalization
│       ├── en.json             # English translations
│       └── ar.json             # Arabic translations
│
└── README.md           # This file
```

## Asset Details

### Images

**icon.ico**
- Format: ICO (multi-resolution)
- Resolutions: 256x256, 128x128, 64x64, 32x32, 16x16
- Purpose: Windows application icon, taskbar icon, file associations

**icon.png**
- Format: PNG with transparency
- Resolution: 256x256
- Purpose: Cross-platform icon, about dialog, macOS dock icon

### Configuration

**default_config.json**
- Default application settings
- Download presets
- Supported platforms list
- Quality and format options

### Translations

**translations/en.json**
- English (default) language file
- Contains all UI strings and messages

**translations/ar.json**
- Arabic language file
- RTL (right-to-left) language support

## Usage in Code

### Accessing Assets
```python
from pathlib import Path

# Get assets directory
ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Load configuration
import json
with open(ASSETS_DIR / "data" / "default_config.json") as f:
    config = json.load(f)

# Load translations
with open(ASSETS_DIR / "data" / "translations" / "en.json") as f:
    translations = json.load(f)

# Load icon
from PIL import Image
icon = Image.open(ASSETS_DIR / "images" / "icon.ico")
```

### Including in Executable

**PyInstaller:**
```bash
pyinstaller --add-data "assets:assets" src/main.py
```

**Nuitka:**
```bash
nuitka --include-data-dir=assets=assets src/main.py
```

## Asset Guidelines

1. **Icons**: Use square dimensions with transparency
2. **Images**: Optimize for size (use PNG for transparency, JPG for photos)
3. **Config**: Keep JSON properly formatted and commented
4. **Translations**: Keep keys consistent across all language files
5. **Documentation**: Update this README when adding new assets

## License

All assets in this directory are part of MediaMagnet and follow the same license as the main project.