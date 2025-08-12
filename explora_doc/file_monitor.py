"""File monitoring and screenshot detection."""

import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp"}


def get_default_screenshot_folder() -> Path:
    """Get the default Windows Screenshots folder for current user."""
    user_profile = os.environ.get("USERPROFILE")
    
    # List of potential screenshot locations to check (in order of preference)
    potential_paths = []
    
    if user_profile:
        user_path = Path(user_profile)
        
        # Check for OneDrive redirected Pictures folder first
        # Common OneDrive patterns
        onedrive_patterns = [
            user_path / "OneDrive - *" / "Pictures" / "Screenshots",
            user_path / "OneDrive" / "Pictures" / "Screenshots",
        ]
        
        # Find actual OneDrive folders using glob
        for pattern in onedrive_patterns:
            for onedrive_path in user_path.glob(str(pattern.relative_to(user_path))):
                if onedrive_path.exists():
                    potential_paths.append(onedrive_path)
        
        # Add standard local Pictures folder
        potential_paths.append(user_path / "Pictures" / "Screenshots")
    else:
        # Fallback if USERPROFILE is not available
        user = os.getlogin()
        potential_paths.append(Path(f"C:/Users/{user}/Pictures/Screenshots"))
    
    for path in potential_paths:
        if path.exists() and any(path.iterdir()):  # Check if folder exists and has files
            return path
        elif path.exists():  # Empty but exists
            return path

    # If no existing path found, return the first potential path or a default location
    if potential_paths:
        return potential_paths[0]
    # Fallback to user's Pictures/Screenshots folder
    user = os.environ.get("USERPROFILE") or os.getlogin()
    return Path(f"C:/Users/{user}/Pictures/Screenshots")


class ScreenshotHandler(FileSystemEventHandler):
    """File system event handler for detecting new screenshots."""
    
    def __init__(self, callback):
        """Initialize with callback function for new images."""
        super().__init__()
        self.callback = callback

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix.lower() in SUPPORTED_EXTS:
            self.callback(file_path)


class FileMonitor:
    """Manages file system monitoring for new screenshots."""
    
    def __init__(self):
        self.observer = None
        self._callback = None
    
    def start_monitoring(self, folder_path: Path, callback):
        """Start monitoring the specified folder for new images."""
        if self.observer is not None:
            self.stop_monitoring()
        
        self._callback = callback
        handler = ScreenshotHandler(callback)
        self.observer = Observer()
        self.observer.schedule(handler, str(folder_path), recursive=False)
        self.observer.start()
    
    def stop_monitoring(self):
        """Stop file monitoring."""
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2)
            except Exception:
                pass
            finally:
                self.observer = None
    
    @property
    def is_monitoring(self) -> bool:
        """Check if currently monitoring."""
        return self.observer is not None and self.observer.is_alive()
