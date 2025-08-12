# Assets Directory

This directory contains UI assets for the ExploraDoc desktop application.

## Directory Structure

```
assets/
├── __init__.py          # Asset management utilities
├── icons/               # Application icons and UI icons
│   ├── app_icon.ico     # Main application icon (Windows)
│   ├── app_icon.png     # Main application icon (cross-platform)
│   ├── folder.png       # Folder icon for UI buttons
│   ├── export.png       # Export icon
│   ├── clear.png        # Clear/delete icon
│   ├── start.png        # Start/play icon
│   └── stop.png         # Stop icon
└── images/              # Other UI images
    ├── logo.png         # Application logo
    ├── splash.png       # Splash screen image (if needed)
    └── banner.png       # Header banner (if needed)
```

## Usage

Import the asset utilities in your UI code:

```python
from explora_doc.assets import get_icon_path, get_image_path

# Get icon paths
app_icon = get_icon_path("app_icon.png")
folder_icon = get_icon_path("folder.png")

# Get image paths
logo = get_image_path("logo.png")
```

## Asset Guidelines

### Icons
- **Format**: PNG with transparent background preferred
- **Size**: Multiple sizes recommended (16x16, 32x32, 48x48, 64x64, 128x128)
- **Style**: Consistent with the application's design language
- **Naming**: Use descriptive names with underscores (e.g., `folder_open.png`)

### Images
- **Format**: PNG for graphics with transparency, JPG for photos
- **Size**: Optimize for display resolution while keeping file size reasonable
- **Quality**: High enough for crisp display on modern screens

### Application Icon
- **Windows**: Include .ico file for proper Windows integration
- **Cross-platform**: PNG version for other platforms
- **Sizes**: Include multiple resolutions in the .ico file (16, 32, 48, 64, 128, 256 pixels)

## Implementation Notes

- Assets are loaded using the utility functions to ensure proper path resolution
- All paths are relative to the assets directory
- The asset loader handles both development and packaged application scenarios
