# Images Directory

This directory should contain larger images and graphics for the ExploraDoc application:

## Suggested Images

### Branding
- `logo.png` - Application logo (for about dialogs, headers)
- `logo_horizontal.png` - Horizontal version of logo
- `logo_icon.png` - Icon-only version of logo

### UI Graphics
- `splash.png` - Splash screen image (if implementing splash screen)
- `banner.png` - Header banner for main window
- `background.png` - Background pattern or texture (if needed)

### Help/Tutorial
- `tutorial_*.png` - Screenshots for help documentation
- `placeholder.png` - Placeholder image for empty states

## Image Guidelines

- **Format**: PNG for graphics with transparency, JPG for photos
- **Quality**: High resolution (2x size for retina displays)
- **Optimization**: Compress images to keep file sizes reasonable
- **Consistency**: Maintain consistent style and color scheme

## Usage

Load images using the asset utility functions:

```python
from explora_doc.assets import get_image_path

logo_path = get_image_path("logo.png")
banner_path = get_image_path("banner.png")
```
