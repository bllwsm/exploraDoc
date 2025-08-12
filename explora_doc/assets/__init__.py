"""Assets package for ExploraDoc UI resources."""

from pathlib import Path

# Base assets directory
ASSETS_DIR = Path(__file__).parent

# Subdirectories
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"

def get_asset_path(asset_name: str, asset_type: str = "icons") -> Path:
    """
    Get the full path to an asset file.
    
    Args:
        asset_name: Name of the asset file (e.g., 'logo.png')
        asset_type: Type of asset ('icons' or 'images')
        
    Returns:
        Path to the asset file
    """
    if asset_type == "icons":
        return ICONS_DIR / asset_name
    elif asset_type == "images":
        return IMAGES_DIR / asset_name
    else:
        raise ValueError(f"Unknown asset type: {asset_type}")

def get_icon_path(icon_name: str) -> Path:
    """Get path to an icon file."""
    return get_asset_path(icon_name, "icons")

def get_image_path(image_name: str) -> Path:
    """Get path to an image file."""
    return get_asset_path(image_name, "images")
