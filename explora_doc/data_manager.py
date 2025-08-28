"""Data persistence manager for ExploraDoc application."""

import json
import tkinter as tk
from pathlib import Path
from typing import Dict, Any
from dataclasses import asdict
from .models import ScreenshotMeta, TestingCharter


class DataManager:
    """Handles saving and loading application data."""
    
    def __init__(self, data_file: Path = None):
        """Initialize the data manager with a specific data file."""
        if data_file is None:
            # Default to a data file in the user's Documents folder
            documents_path = Path.home() / "Documents"
            self.data_file = documents_path / "ExploraDoc" / "session_data.json"
        else:
            self.data_file = data_file
        
        # Ensure the directory exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, screenshots: Dict[Path, ScreenshotMeta], test_title: str = "", 
                     testing_charter: TestingCharter | None = None,
                     test_type: str | None = None) -> None:
        """Save the current session data to file."""
        try:
            # Convert screenshots data to serializable format
            serializable_data = {
                "test_title": test_title,
                "test_type": test_type or "",
                "testing_charter": {},
                "screenshots": []
            }
            
            # Serialize testing charter if provided
            if testing_charter is not None:
                serializable_data["testing_charter"] = {
                    "enabled": bool(testing_charter.enabled.get()),
                    "objective": testing_charter.objective.get(),
                    "whats_checked": testing_charter.whats_checked.get(),
                    "prerequisites": testing_charter.prerequisites.get(),
                    "exclusions": testing_charter.exclusions.get(),
                    "defects": testing_charter.defects.get(),
                    "peer_review": testing_charter.peer_review.get(),
                }
            
            for path, meta in screenshots.items():
                screenshot_data = {
                    "path": str(path),
                    "what": meta.what.get(),
                    "caption": meta.caption.get()
                }
                serializable_data["screenshots"].append(screenshot_data)
            
            # Write to file
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving session data: {e}")
    
    def load_session(self) -> tuple[Dict[Path, ScreenshotMeta], str, dict, str]:
        """Load session data from file."""
        screenshots = {}
        test_title = ""
        charter_data: dict = {}
        test_type: str = ""
        
        try:
            if not self.data_file.exists():
                return screenshots, test_title, charter_data, test_type
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_title = data.get("test_title", "")
            test_type = data.get("test_type", "")
            charter_data = data.get("testing_charter", {}) or {}
            
            for screenshot_data in data.get("screenshots", []):
                path = Path(screenshot_data["path"])
                
                # Only load if the file still exists
                if path.exists():
                    meta = ScreenshotMeta(path=path)
                    meta.what.set(screenshot_data.get("what", ""))
                    meta.caption.set(screenshot_data.get("caption", ""))
                    screenshots[path] = meta
                    
        except Exception as e:
            print(f"Error loading session data: {e}")
        
        return screenshots, test_title, charter_data, test_type
    
    def clear_session_file(self) -> None:
        """Remove the session data file."""
        try:
            if self.data_file.exists():
                self.data_file.unlink()
        except Exception as e:
            print(f"Error clearing session file: {e}")
    
    def has_saved_session(self) -> bool:
        """Check if there's a saved session file."""
        return self.data_file.exists() and self.data_file.stat().st_size > 0
