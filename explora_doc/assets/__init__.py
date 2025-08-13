"""Asset management for ExploraDoc."""

from pathlib import Path


def get_icon_path(icon_name: str) -> Path:
    """Get the path to an icon file."""
    assets_dir = Path(__file__).parent
    icon_path = assets_dir / "icons" / icon_name
    return icon_path


def get_image_path(image_name: str) -> Path:
    """Get the path to an image file."""
    assets_dir = Path(__file__).parent
    image_path = assets_dir / "images" / image_name
    return image_path