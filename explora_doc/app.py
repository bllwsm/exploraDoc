"""ExploraDoc - A lightweight tool for exploratory testing documentation."""

import queue
import time
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from typing import Dict
from tkinter import messagebox, filedialog
from PIL import Image

from .models import ScreenshotMeta, TestingCharter
from .file_monitor import FileMonitor, get_default_screenshot_folder
from .exporter import DocumentExporter
from .ui import MainUI, ScreenshotEntryUI, ImageViewerDialog, ExportSuccessDialog
from .data_manager import DataManager
from .image_editor import ImageAnnotationEditor


class ExploraDocApp:
    """Main application controller for ExploraDoc."""
    
    def __init__(self, root: ctk.CTk):
        self.root = root
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Application state - initialize before UI
        self.screenshots: Dict[Path, ScreenshotMeta] = {}
        self.selected_folder: Path = get_default_screenshot_folder()
        self.event_queue: queue.Queue = queue.Queue()
        self.testing_charter = TestingCharter()  # Initialize testing charter
        
        # Create UI after screenshots is initialized
        self.ui = MainUI(root, self)
        
        # File monitoring
        self.file_monitor = FileMonitor()
        
        # Load saved session data
        self._load_session_data()
        
        # Initialize UI
        self.ui.update_folder_display(self.selected_folder)
        self._start_queue_polling()
        
        # Auto-save session data periodically
        self._schedule_auto_save()
    
    def start_monitoring(self):
        """Start monitoring the selected folder for new screenshots."""
        if self.file_monitor.is_monitoring:
            return
        
        if not self.selected_folder.exists():
            messagebox.showerror(
                "Folder Missing", 
                f"Screenshots folder not found: {self.selected_folder}\n"
                "Create it and try again."
            )
            return
        
        self.file_monitor.start_monitoring(
            self.selected_folder, 
            self._on_new_screenshot
        )
        self.ui.set_monitoring_state(True)
    
    def stop_monitoring(self):
        """Stop monitoring for new screenshots."""
        self.file_monitor.stop_monitoring()
        self.ui.set_monitoring_state(False)
    
    def change_folder(self):
        """Allow user to select a different screenshot folder."""
        if self.file_monitor.is_monitoring:
            return
        
        initial_dir = (
            self.selected_folder 
            if self.selected_folder.exists() 
            else get_default_screenshot_folder().parent
        )
        
        chosen = filedialog.askdirectory(
            title="Select Screenshot Folder", 
            initialdir=str(initial_dir)
        )
        
        if not chosen:
            return
        
        new_path = Path(chosen)
        if not new_path.exists():
            messagebox.showerror(
                "Invalid Folder", 
                "Selected folder does not exist."
            )
            return
        
        self.selected_folder = new_path
        self.ui.update_folder_display(new_path)
    
    def export_to_word(self):
        """Export all screenshots and annotations to a Word document."""
        if not self.screenshots:
            messagebox.showinfo("Nothing to Export", "No screenshots to export.")
            return
        
        # Validate all required fields before export
        validation_errors = self.ui.validate_all_fields()
        if validation_errors:
            error_message = "Please fill in all required fields:\n\n" + "\n".join(validation_errors)
            messagebox.showerror("Validation Error", error_message)
            return

        try:
            test_title = self.ui.test_title_var.get().strip() or "Exploratory Test Session"
            test_type = self.ui.test_type_var.get() or "Exploratory"
            file_path = DocumentExporter.export_to_word(
                self.screenshots, test_title, self.testing_charter, test_type
            )
            ExportSuccessDialog.show_success(self.root, file_path)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
    
    def clear_session(self):
        """Clear all screenshots and annotations from the session."""
        if not messagebox.askyesno(
            "Confirm", 
            "Clear all screenshots and annotations?"
        ):
            return
        
        self.ui.clear_screenshot_feed()
        self.screenshots.clear()
        # Clear the saved session file
        self.data_manager.clear_session_file()
        # Update button states when screenshots are cleared
        self.ui._update_button_states()
    
    def delete_screenshot(self, meta: ScreenshotMeta):
        """Delete a specific screenshot entry."""
        if not messagebox.askyesno(
            "Confirm Delete", 
            "Delete this screenshot entry?"
        ):
            return
        
        # Remove from screenshots dictionary
        if meta.path in self.screenshots:
            del self.screenshots[meta.path]
        
        # Remove the UI element
        if meta.entry_frame:
            meta.entry_frame.destroy()
        
        # Save the updated data
        self._save_session_data()
        
        # Update button states
        self.ui._update_button_states()
    
    def shutdown(self):
        """Clean shutdown of the application."""
        # Save session data before closing
        self._save_session_data()
        self.file_monitor.stop_monitoring()
        self.root.destroy()
    
    def _on_new_screenshot(self, file_path: Path):
        """Handle new screenshot detection."""
        self.event_queue.put(("new_image", file_path))
    
    def _start_queue_polling(self):
        """Start polling the event queue for new screenshots."""
        self._poll_queue()
    
    def _poll_queue(self):
        """Poll the event queue for new screenshot notifications."""
        try:
            while True:
                event_type, file_path = self.event_queue.get_nowait()
                if event_type == "new_image":
                    self._add_screenshot(file_path)
        except queue.Empty:
            pass
        finally:
            self.root.after(400, self._poll_queue)
    
    def _add_screenshot(self, file_path: Path):
        """Add a new screenshot to the UI with retry logic for file availability."""
        if file_path in self.screenshots:
            return
        
        # Try to open the image with retry logic for OneDrive/file locks
        image = self._try_open_image_with_retry(file_path)
        if image is None:
            return  # Failed to open after retries
        
        meta = ScreenshotMeta(path=file_path)
        ScreenshotEntryUI(
            self.ui.feed_frame, 
            meta, 
            image, 
            self._show_full_image,
            self  # Pass controller reference
        )
        self.screenshots[file_path] = meta
        
        # Save session data when new screenshot is added
        self._save_session_data()
        
        # Update button states when screenshot is added
        self.ui._update_button_states()
    
    def _try_open_image_with_retry(self, file_path: Path, max_attempts: int = 10) -> Image.Image | None:
        """Try to open an image file with retry logic for OneDrive/file locks.
        
        Args:
            file_path: Path to the image file
            max_attempts: Maximum number of retry attempts
            
        Returns:
            PIL Image object if successful, None if all attempts failed
        """
        for attempt in range(max_attempts):
            try:
                return Image.open(file_path)
            except (OSError, PermissionError, FileNotFoundError) as e:
                if attempt == max_attempts - 1:
                    # Last attempt failed
                    print(f"Failed to open {file_path} after {max_attempts} attempts: {e}")
                    return None
                
                # Wait before retrying, with increasing delay
                wait_time = 0.2 + (attempt * 0.2)  # 0.2s, 0.4s, 0.6s, etc.
                time.sleep(wait_time)
                
        return None
    
    def _show_full_image(self, file_path: Path):
        """Open the image annotation editor."""
        self.open_image_editor(file_path)
    
    def open_image_editor(self, file_path: Path):
        """Open the image annotation editor for the given image."""
        try:
            ImageAnnotationEditor.open(
                self.root, 
                file_path, 
                on_save_callback=lambda new_path: self._on_image_saved(file_path, new_path)
            )
        except Exception as e:
            messagebox.showerror("Editor Error", f"Failed to open image editor: {e}")
    
    def _on_image_saved(self, original_path: Path, new_path: Path):
        """Handle image save callback from the annotation editor."""
        # Update the screenshot entry to point to the new annotated image
        if original_path in self.screenshots:
            # Get the metadata for the original image
            meta = self.screenshots[original_path]
            
            # Remove the old entry
            del self.screenshots[original_path]
            
            # Update the metadata to point to the new path
            meta.path = new_path
            
            # Add it back with the new path
            self.screenshots[new_path] = meta
            
            # Refresh the entire UI to show the updated image
            self._refresh_screenshot_order()
            
            # Save the updated session data
            self._save_session_data()
    
    def _refresh_screenshot_thumbnails(self):
        """Refresh all screenshot thumbnails to reflect any changes."""
        # This is a simple approach - clear and reload all screenshots
        # In a more sophisticated implementation, we could refresh individual thumbnails
        current_screenshots = dict(self.screenshots)  # Copy current state
        
        # Clear UI
        self.ui.clear_screenshot_feed()
        self.screenshots.clear()
        
        # Reload all screenshots
        for path, meta in current_screenshots.items():
            if path.exists():  # Only reload if file still exists
                try:
                    image = Image.open(path)
                    ScreenshotEntryUI(
                        self.ui.feed_frame, 
                        meta, 
                        image, 
                        self._show_full_image,
                        self
                    )
                    self.screenshots[path] = meta
                except Exception as e:
                    print(f"Error refreshing screenshot {path}: {e}")
                    continue
        
        # Update button states
        self.ui._update_button_states()
    
    def reorder_entry(self, meta: ScreenshotMeta, move_down: bool):
        """Reorder a screenshot entry up or down."""
        # Get current order of screenshots
        screenshot_list = list(self.screenshots.items())
        current_index = next(i for i, (path, m) in enumerate(screenshot_list) if m == meta)
        
        if move_down and current_index < len(screenshot_list) - 1:
            # Move down (swap with next item)
            new_index = current_index + 1
        elif not move_down and current_index > 0:
            # Move up (swap with previous item)
            new_index = current_index - 1
        else:
            return  # No movement needed
        
        # Swap the items
        screenshot_list[current_index], screenshot_list[new_index] = \
            screenshot_list[new_index], screenshot_list[current_index]
        
        # Update the dictionary with new order
        self.screenshots = dict(screenshot_list)
        
        # Refresh the UI
        self._refresh_screenshot_order()
    
    def _refresh_screenshot_order(self):
        """Refresh the UI to show screenshots in the new order."""
        # Clear the current UI
        self.ui.clear_screenshot_feed()
        
        # Re-add all screenshots in the new order
        for path, meta in self.screenshots.items():
            try:
                image = Image.open(path)
                ScreenshotEntryUI(
                    self.ui.feed_frame, 
                    meta, 
                    image, 
                    self._show_full_image,
                    self
                )
            except Exception:
                continue  # Skip invalid images
    
    def _load_session_data(self):
        """Load saved session data if it exists."""
        try:
            screenshots, test_title, charter_data, saved_test_type = self.data_manager.load_session()
            
            # Set the test title
            if test_title:
                self.ui.test_title_var.set(test_title)
            # Set test type if saved
            if saved_test_type:
                self.ui.test_type_var.set(saved_test_type)
            
            # Restore testing charter
            if charter_data:
                try:
                    self.testing_charter.enabled.set(bool(charter_data.get("enabled", False)))
                    self.testing_charter.objective.set(charter_data.get("objective", ""))
                    self.testing_charter.whats_checked.set(charter_data.get("whats_checked", ""))
                    self.testing_charter.prerequisites.set(charter_data.get("prerequisites", ""))
                    self.testing_charter.exclusions.set(charter_data.get("exclusions", ""))
                    self.testing_charter.defects.set(charter_data.get("defects", ""))
                    self.testing_charter.peer_review.set(charter_data.get("peer_review", ""))
                except Exception as e:
                    print(f"Error restoring charter data: {e}")
            
            # Load screenshots
            for path, meta in screenshots.items():
                if path.exists():  # Only load if file still exists
                    try:
                        image = Image.open(path)
                        ScreenshotEntryUI(
                            self.ui.feed_frame, 
                            meta, 
                            image, 
                            self._show_full_image,
                            self
                        )
                        self.screenshots[path] = meta
                    except Exception as e:
                        print(f"Error loading screenshot {path}: {e}")
                        continue
            
            # Update button states
            self.ui._update_button_states()
            # Ensure UI reflects loaded charter content
            try:
                self.ui.refresh_charter_from_model()
            except Exception as e:
                print(f"Error refreshing charter UI: {e}")
            
        except Exception as e:
            print(f"Error loading session data: {e}")
    
    def _save_session_data(self):
        """Save current session data."""
        try:
            test_title = self.ui.test_title_var.get()
            test_type = self.ui.test_type_var.get()
            self.data_manager.save_session(
                self.screenshots,
                test_title,
                testing_charter=self.testing_charter,
                test_type=test_type
            )
        except Exception as e:
            print(f"Error saving session data: {e}")
    
    def _schedule_auto_save(self):
        """Schedule automatic saving of session data."""
        self._save_session_data()
        # Schedule next auto-save in 30 seconds
        self.root.after(30000, self._schedule_auto_save)


def main():
    """Main entry point for the application."""
    root = ctk.CTk()
    app = ExploraDocApp(root)
    root.protocol("WM_DELETE_WINDOW", app.shutdown)
    root.mainloop()


if __name__ == "__main__":
    main()
