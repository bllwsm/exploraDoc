"""UI components for the ExploraDoc application."""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from pathlib import Path
from PIL import Image
import os
import subprocess
import webbrowser

from .models import ScreenshotMeta
from .assets import get_icon_path, get_image_path


THUMBNAIL_SIZE = (180, 120)


class MainUI:
    """Main user interface for the ExploraDoc application."""
    
    def __init__(self, root: ctk.CTk, controller):
        self.root = root
        self.controller = controller
        self.folder_var = tk.StringVar()
        self.test_title_var = tk.StringVar()  # Empty by default, user enters ticket number only
        self.test_type_var = tk.StringVar()  # No default value as specified
        
        # UI References
        self.feed_frame = None
        self.start_btn = None
        self.change_btn = None
        self.export_btn = None
        self.clear_btn = None
        
        self._setup_window()
        self._build_interface()
    
    def _load_icon(self, icon_name: str, size: tuple = (20, 20)) -> ctk.CTkImage:
        """
        Load an icon from the assets directory.
        
        Args:
            icon_name: Name of the icon file
            size: Size tuple for the icon (width, height)
            
        Returns:
            CTkImage object or None if icon not found
        """
        try:
            icon_path = get_icon_path(icon_name)
            if icon_path.exists():
                img = Image.open(icon_path)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception as e:
            print(f"Warning: Could not load icon '{icon_name}': {e}")
        return None
    
    def _setup_window(self):
        """Configure the main window."""
        # Set CustomTkinter appearance
        ctk.set_appearance_mode("system")  # "dark", "light", "system"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        self.root.title("ExploraDoc")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)  # Set minimum window size
        self.root.maxsize(2400, 1000)  # Set maximum window size
        
        # Try to set application icon
        try:
            icon_path = get_icon_path("app_icon.png")
            if icon_path.exists():
                img = Image.open(icon_path)
                icon = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
                # Note: CTk doesn't directly support window icons, but we can try tkinter method
                try:
                    self.root.iconphoto(True, img)
                except:
                    pass  # Silently fail if icon setting doesn't work
        except Exception:
            pass  # Silently fail if no icon available
    
    def _build_interface(self):
        """Build the main user interface."""
        self._create_test_title_section()
        self._create_toolbar()
        self._create_testing_charter_section()
        self._create_screenshot_feed()
    
    def _create_test_title_section(self):
        """Create the test title input section."""
        title_frame = ctk.CTkFrame(self.root)
        title_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 5))
        
        # Test type dropdown
        self.test_type_dropdown = ctk.CTkComboBox(
            title_frame,
            variable=self.test_type_var,
            values=["QA", "Exploratory"],
            state="readonly",
            width=100,
            command=self._on_test_type_change
        )
        self.test_type_dropdown.pack(side=tk.LEFT, padx=(10, 5), pady=10)
        
        ctk.CTkLabel(
            title_frame, 
            text="Ticket Number: *",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side=tk.LEFT, padx=(0, 5), pady=10)
        
        self.title_entry = ctk.CTkEntry(
            title_frame, 
            textvariable=self.test_title_var, 
            width=200,
            placeholder_text="AS-22280 (Required)"
        )
        self.title_entry.pack(side=tk.LEFT, padx=(0, 10), pady=10)
        
        # Bind validation to the entry
        self.test_title_var.trace_add("write", self._validate_title_field)
        self.test_title_var.trace_add("write", self._on_title_change)
        self.test_title_var.trace_add("write", self._enforce_character_limit)
    
    def _on_test_type_change(self, value):
        """Handle test type dropdown selection and update placeholder text."""
        # Placeholder text remains consistent since user only enters ticket number
        self.title_entry.configure(placeholder_text="AS-22280 (Required)")
    
    def _create_toolbar(self):
        """Create the top toolbar with controls."""
        toolbar = ctk.CTkFrame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Folder selection
        folder_entry = ctk.CTkEntry(
            toolbar, 
            textvariable=self.folder_var, 
            width=400, 
            state="readonly",
            placeholder_text="No folder selected..."
        )
        folder_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.change_btn = ctk.CTkButton(
            toolbar, 
            text="Change Folder",
            image=self._load_icon("folder.png", (20, 20)),
            command=self.controller.change_folder,
            width=140
        )
        # Fallback to emoji if no icon
        if self.change_btn.cget("image") is None:
            self.change_btn.configure(text="📁 Change Folder")
        self.change_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Control buttons
        self.start_btn = ctk.CTkButton(
            toolbar, 
            text="Start Test",
            image=self._load_icon("start.png", (20, 20)),
            command=self.controller.start_monitoring,
            fg_color="#2b9348",
            hover_color="#207a3c",
            width=120
        )
        # Fallback to emoji if no icon
        if self.start_btn.cget("image") is None:
            self.start_btn.configure(text="🎯 Start Test")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ctk.CTkButton(
            toolbar, 
            text="Export",
            image=self._load_icon("export.png", (20, 20)),
            command=self.controller.export_to_word, 
            width=100
        )
        # Fallback to emoji if no icon
        if self.export_btn.cget("image") is None:
            self.export_btn.configure(text="📄 Export")
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ctk.CTkButton(
            toolbar, 
            text="Clear",
            image=self._load_icon("clear.png", (20, 20)),
            command=self.controller.clear_session, 
            fg_color="#dc3545",
            hover_color="#c82333",
            width=100
        )
        # Fallback to emoji if no icon
        if self.clear_btn.cget("image") is None:
            self.clear_btn.configure(text="🗑️ Clear")
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Initialize button states
        self._update_button_states()
    
    def _create_testing_charter_section(self):
        """Create the testing charter section with separate dropdown and export toggle."""
        # Main container
        self.charter_frame = ctk.CTkFrame(self.root)
        self.charter_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(2, 5))

        # Header with dropdown button and export toggle
        header_frame = ctk.CTkFrame(self.charter_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=2)

        # Dropdown button for UI visibility
        self.charter_expanded = tk.BooleanVar(value=True)  # Start expanded
        self.charter_dropdown_btn = ctk.CTkButton(
            header_frame,
            text="▼ Testing Charter",
            width=130,
            height=24,
            command=self._toggle_charter_visibility
        )
        self.charter_dropdown_btn.pack(side=tk.LEFT, padx=(5, 8))

        # Export inclusion toggle
        self.charter_export_toggle = ctk.CTkSwitch(
            header_frame,
            text="Include in Export",
            variable=self.controller.testing_charter.enabled,
            command=self._on_export_toggle_change
        )
        self.charter_export_toggle.pack(side=tk.LEFT)

        # Charter content area (initially visible)
        self.charter_content_frame = ctk.CTkFrame(self.charter_frame)
        self.charter_content_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self._create_charter_fields()

    def _create_charter_fields(self):
        """Create the individual charter fields."""
        # Objective (*)
        obj_label = ctk.CTkLabel(
            self.charter_content_frame,
            text="Objective: *",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        obj_label.pack(anchor="w", padx=8, pady=(5, 1))

        obj_entry = ctk.CTkEntry(
            self.charter_content_frame,
            textvariable=self.controller.testing_charter.objective,
            placeholder_text="Enter test objective...",
            height=28
        )
        obj_entry.pack(fill=tk.X, padx=8, pady=(0, 5))

        # What's going to be checked (*) - Interactive bullet points
        checked_label = ctk.CTkLabel(
            self.charter_content_frame,
            text="What's going to be checked: *",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        checked_label.pack(anchor="w", padx=8, pady=(2, 1))

        # Container for bullet points
        self.bullet_container = ctk.CTkFrame(self.charter_content_frame)
        self.bullet_container.pack(fill=tk.X, padx=8, pady=(0, 5))
        
        # List to track bullet point entries
        self.bullet_entries = []
        
        # Entry for adding new bullet points
        self.new_bullet_frame = ctk.CTkFrame(self.bullet_container)
        self.new_bullet_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ctk.CTkLabel(
            self.new_bullet_frame,
            text="•",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=tk.LEFT, padx=(5, 2))
        
        self.new_bullet_entry = ctk.CTkEntry(
            self.new_bullet_frame,
            placeholder_text="Press Enter to add bullet point...",
            height=28
        )
        self.new_bullet_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.new_bullet_entry.bind("<Return>", self._add_bullet_point)
        
        # Initially add the textbox but hide it (for backwards compatibility with data loading)
        self.checked_textbox = ctk.CTkTextbox(
            self.charter_content_frame,
            height=0  # Hidden
        )
        # Still bind to StringVar for data persistence
        self.checked_textbox.bind("<KeyRelease>", self._update_checked_text)

        # Prerequisites
        prereq_label = ctk.CTkLabel(
            self.charter_content_frame,
            text="Prerequisites:",
            font=ctk.CTkFont(size=11)
        )
        prereq_label.pack(anchor="w", padx=8, pady=(2, 1))

        prereq_entry = ctk.CTkEntry(
            self.charter_content_frame,
            textvariable=self.controller.testing_charter.prerequisites,
            placeholder_text="List any prerequisites...",
            height=28
        )
        prereq_entry.pack(fill=tk.X, padx=8, pady=(0, 5))

        # Exclusions
        excl_label = ctk.CTkLabel(
            self.charter_content_frame,
            text="Exclusions:",
            font=ctk.CTkFont(size=11)
        )
        excl_label.pack(anchor="w", padx=8, pady=(2, 1))

        excl_entry = ctk.CTkEntry(
            self.charter_content_frame,
            textvariable=self.controller.testing_charter.exclusions,
            placeholder_text="List any exclusions...",
            height=28
        )
        excl_entry.pack(fill=tk.X, padx=8, pady=(0, 5))

        # Defects
        defects_label = ctk.CTkLabel(
            self.charter_content_frame,
            text="Defects:",
            font=ctk.CTkFont(size=11)
        )
        defects_label.pack(anchor="w", padx=8, pady=(2, 1))

        defects_entry = ctk.CTkEntry(
            self.charter_content_frame,
            textvariable=self.controller.testing_charter.defects,
            placeholder_text="List known defects...",
            height=28
        )
        defects_entry.pack(fill=tk.X, padx=8, pady=(0, 5))

        # Peer Review (single line)
        review_label = ctk.CTkLabel(
            self.charter_content_frame,
            text="Peer Review:",
            font=ctk.CTkFont(size=11)
        )
        review_label.pack(anchor="w", padx=8, pady=(2, 1))

        review_entry = ctk.CTkEntry(
            self.charter_content_frame,
            textvariable=self.controller.testing_charter.peer_review,
            placeholder_text="Peer review status...",
            height=28
        )
        review_entry.pack(fill=tk.X, padx=8, pady=(0, 5))
        
        # Load any existing bullet points from saved data
        self.root.after(100, self._load_existing_bullet_points)  # Small delay to ensure UI is ready

    def _toggle_charter_visibility(self):
        """Handle dropdown button click to show/hide charter fields."""
        if self.charter_expanded.get():
            # Collapse
            self.charter_content_frame.pack_forget()
            self.charter_dropdown_btn.configure(text="▲ Testing Charter")
            self.charter_expanded.set(False)
        else:
            # Expand
            self.charter_content_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            self.charter_dropdown_btn.configure(text="▼ Testing Charter")
            self.charter_expanded.set(True)

    def _on_export_toggle_change(self):
        """Handle export toggle change - just update validation state."""
        # The export toggle only affects whether charter is included in export
        # UI visibility is controlled separately by the dropdown
        self._update_button_states()

    def _add_bullet_point(self, event=None):
        """Add a new bullet point when Enter is pressed."""
        text = self.new_bullet_entry.get().strip()
        if text:
            self._create_bullet_point_widget(text)
            self.new_bullet_entry.delete(0, tk.END)
            self._update_bullet_text()
    
    def _create_bullet_point_widget(self, text):
        """Create a widget for a single bullet point with edit/delete options."""
        bullet_frame = ctk.CTkFrame(self.bullet_container)
        bullet_frame.pack(fill=tk.X, padx=5, pady=2, before=self.new_bullet_frame)
        
        # Bullet symbol
        ctk.CTkLabel(
            bullet_frame,
            text="•",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=tk.LEFT, padx=(5, 2))
        
        # Entry for editing
        entry = ctk.CTkEntry(
            bullet_frame,
            height=28
        )
        entry.insert(0, text)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        entry.bind("<KeyRelease>", lambda e: self._update_bullet_text())
        entry.bind("<Return>", lambda e: entry.master.focus())  # Remove focus on Enter
        
        # Delete button
        delete_btn = ctk.CTkButton(
            bullet_frame,
            text="×",
            width=25,
            height=25,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="red",
            hover_color="darkred",
            command=lambda: self._delete_bullet_point(bullet_frame)
        )
        delete_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Store reference
        self.bullet_entries.append((bullet_frame, entry))
    
    def _delete_bullet_point(self, bullet_frame):
        """Delete a bullet point."""
        # Remove from tracking list
        self.bullet_entries = [(frame, entry) for frame, entry in self.bullet_entries if frame != bullet_frame]
        # Destroy the widget
        bullet_frame.destroy()
        self._update_bullet_text()
    
    def _update_bullet_text(self):
        """Update the underlying StringVar with current bullet points."""
        bullet_texts = []
        for frame, entry in self.bullet_entries:
            text = entry.get().strip()
            if text:
                bullet_texts.append(f"- {text}")
        
        # Update the StringVar (this maintains compatibility with export)
        combined_text = '\n'.join(bullet_texts)
        self.controller.testing_charter.whats_checked.set(combined_text)
        
        # Also update the hidden textbox for backwards compatibility
        self.checked_textbox.delete("1.0", tk.END)
        self.checked_textbox.insert("1.0", combined_text)

    def _load_existing_bullet_points(self):
        """Load existing bullet points from saved data."""
        existing_text = self.controller.testing_charter.whats_checked.get()
        if existing_text:
            lines = existing_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    bullet_text = line[2:].strip()
                    if bullet_text:
                        self._create_bullet_point_widget(bullet_text)
                elif line:  # Non-bullet line, add as is
                    self._create_bullet_point_widget(line)

    def _update_checked_text(self, event=None):
        """Update the what's checked StringVar from textbox."""
        content = self.checked_textbox.get("1.0", tk.END).strip()
        self.controller.testing_charter.whats_checked.set(content)
    
    def _create_screenshot_feed(self):
        """Create the scrollable screenshot feed area."""
        # Create main container frame
        container = ctk.CTkFrame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create scrollable frame for screenshots
        self.feed_frame = ctk.CTkScrollableFrame(
            container,
            label_text="Test Evidence",
            label_font=ctk.CTkFont(size=16, weight="bold")
        )
        self.feed_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def update_folder_display(self, folder_path: Path):
        """Update the folder path display."""
        self.folder_var.set(str(folder_path))
    
    def set_monitoring_state(self, monitoring: bool):
        """Update UI state based on monitoring status."""
        if monitoring:
            # Change start button to stop button (red color)
            stop_icon = self._load_icon("stop.png", (20, 20))
            self.start_btn.configure(
                text="Stop Test" if stop_icon else "⏹️ Stop Test",
                image=stop_icon,
                command=self.controller.stop_monitoring,
                fg_color="#dc3545",
                hover_color="#c82333"
            )
            self.change_btn.configure(state=tk.DISABLED)
        else:
            # Change back to start button (green color)
            start_icon = self._load_icon("start.png", (20, 20))
            self.start_btn.configure(
                text="Start Test" if start_icon else "🎯 Start Test",
                image=start_icon,
                command=self.controller.start_monitoring,
                fg_color="#2b9348",
                hover_color="#207a3c"
            )
            self.change_btn.configure(state=tk.NORMAL)
        
        # Always update button states based on content
        self._update_button_states()
    
    def _update_button_states(self):
        """Update export and clear button states based on whether there are screenshots."""
        has_screenshots = len(self.controller.screenshots) > 0
        state = tk.NORMAL if has_screenshots else tk.DISABLED
        self.export_btn.configure(state=state)
        self.clear_btn.configure(state=state)
    
    def clear_screenshot_feed(self):
        """Remove all screenshot entries from the UI."""
        for child in list(self.feed_frame.children.values()):
            child.destroy()
    
    def _validate_title_field(self, *args):
        """Validate the ticket number field."""
        ticket_number = self.test_title_var.get().strip()
        
        if not ticket_number:
            self.title_entry.configure(border_color=("red", "red"))
            return
        
        # Check if ticket number starts with "AS-" (case-insensitive)
        if not ticket_number.lower().startswith("as-"):
            self.title_entry.configure(border_color=("red", "red"))
            return

        # Check if ticket number is no more than 13 characters
        if len(ticket_number) > 13:
            self.title_entry.configure(border_color=("red", "red"))
            return
        
        # All validations passed
        self.title_entry.configure(border_color=("gray", "gray"))
    
    def _enforce_character_limit(self, *args):
        """Enforce 13 character limit on ticket number field."""
        current_value = self.test_title_var.get()
        if len(current_value) > 13:
            # Truncate to 13 characters
            self.test_title_var.set(current_value[:13])

    def _on_title_change(self, *args):
        """Handle title field change to trigger auto-save."""
        # Trigger auto-save with a small delay to avoid too frequent saves
        if hasattr(self.controller, '_save_session_data'):
            self.controller.root.after(2000, self.controller._save_session_data)
    
    def validate_all_fields(self):
        """Validate all required fields in the form."""
        errors = []
        
        # Validate ticket number
        ticket_number = self.test_title_var.get().strip()
        if not ticket_number:
            errors.append("Ticket Number is required")
            self.title_entry.configure(border_color=("red", "red"))
        elif not ticket_number.lower().startswith("as-"):
            errors.append("Ticket Number must start with 'AS-'")
            self.title_entry.configure(border_color=("red", "red"))
        elif len(ticket_number) > 13:
            errors.append("Ticket Number must be no more than 13 characters")
            self.title_entry.configure(border_color=("red", "red"))
        else:
            self.title_entry.configure(border_color=("gray", "gray"))
        
        # Validate testing charter if enabled
        if self.controller.testing_charter.enabled.get():
            charter_errors = self._validate_testing_charter()
            errors.extend(charter_errors)
        
        # Validate screenshot entries
        for screenshot_meta in self.controller.screenshots.values():
            screenshot_errors = self._validate_screenshot_entry(screenshot_meta)
            errors.extend(screenshot_errors)
        
        return errors
    
    def _validate_screenshot_entry(self, meta):
        """Validate a single screenshot entry."""
        errors = []
        
        # Validate caption
        if not meta.caption.get().strip():
            errors.append(f"Figure caption is required for screenshot: {meta.path.name}")
        
        # Validate what field
        if not meta.what.get().strip():
            errors.append(f"'What this image shows' is required for screenshot: {meta.path.name}")
        
        # Branch is already required by default value and dropdown, so no need to validate
        
        return errors
    
    def _validate_testing_charter(self):
        """Validate testing charter fields when enabled."""
        errors = []
        charter = self.controller.testing_charter
        
        # Validate required fields
        if not charter.objective.get().strip():
            errors.append("Testing Charter Objective is required")
        
        if not charter.whats_checked.get().strip():
            errors.append("Testing Charter 'What's going to be checked' is required")
        
        return errors


class ScreenshotEntryUI:
    """UI component for individual screenshot entries."""
    
    def __init__(self, parent_frame: ctk.CTkScrollableFrame, meta: ScreenshotMeta, 
                 image: Image.Image, on_thumbnail_click, controller):
        self.meta = meta
        self.on_thumbnail_click = on_thumbnail_click
        self.controller = controller
        self._create_entry(parent_frame, image)
    
    def _create_entry(self, parent_frame: ctk.CTkScrollableFrame, image: Image.Image):
        """Create the UI entry for this screenshot."""
        # Create card-like container for each screenshot
        row = ctk.CTkFrame(parent_frame)
        row.pack(fill=tk.X, padx=10, pady=8)
        
        # Store reference to the frame in the meta object for drag/drop
        self.meta.entry_frame = row
        
        self._create_thumbnail_section(row, image)
        self._create_annotation_fields(row)
        self._create_action_buttons(row)
        self._setup_drag_and_drop(row)
    
    def _create_thumbnail_section(self, row: ctk.CTkFrame, image: Image.Image):
        """Create the thumbnail and caption section on the left."""
        # Left side container for thumbnail and caption
        left_frame = ctk.CTkFrame(row)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Create thumbnail
        thumb = image.copy()
        thumb.thumbnail(THUMBNAIL_SIZE)
        
        # Convert PIL image to CTkImage
        ctk_image = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=THUMBNAIL_SIZE)
        
        btn = ctk.CTkButton(
            left_frame, 
            image=ctk_image,
            text="",  # No text, just image
            command=lambda: self.on_thumbnail_click(self.meta.path),
            width=THUMBNAIL_SIZE[0],
            height=THUMBNAIL_SIZE[1],
            fg_color="transparent",
            hover_color=("gray75", "gray25")
        )
        btn.pack(pady=(0, 5))
        
        # Compact caption field under thumbnail
        self.caption_entry = ctk.CTkEntry(
            left_frame, 
            textvariable=self.meta.caption, 
            placeholder_text="Figure caption... (Required)",
            height=24,
            width=THUMBNAIL_SIZE[0],
            font=ctk.CTkFont(size=11)
        )
        self.caption_entry.pack()
        
        # Bind validation to the caption entry
        self.meta.caption.trace_add("write", self._validate_caption_field)
        self.meta.caption.trace_add("write", self._on_field_change)
    
    def _create_annotation_fields(self, row: ctk.CTkFrame):
        """Create the annotation input fields."""
        # Right side container for fields
        fields_frame = ctk.CTkFrame(row)
        fields_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        # What field (single line)
        ctk.CTkLabel(
            fields_frame, 
            text="What this image shows: *",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.what_entry = ctk.CTkEntry(
            fields_frame, 
            textvariable=self.meta.what, 
            placeholder_text="Describe what is shown in this screenshot... (Required)",
            height=32
        )
        self.what_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        # Bind validation to the what entry
        self.meta.what.trace_add("write", self._validate_what_field)
        self.meta.what.trace_add("write", self._on_field_change)
        
        # Branch selection removed as per requirements
    
    def _create_action_buttons(self, row: ctk.CTkFrame):
        """Create action buttons (delete, etc.) on the right side."""
        # Right side container for action buttons
        actions_frame = ctk.CTkFrame(row)
        actions_frame.pack(side=tk.RIGHT, padx=(5, 10), pady=10)
        
        # Delete button with trash icon
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=24,
            height=24,
            command=self._on_delete_click,
            fg_color="#dc3545",  # Bootstrap danger red
            hover_color="#c82333",  # Darker red on hover
            font=ctk.CTkFont(size=12),
            corner_radius=4
        )
        delete_btn.pack(pady=1)
        
        # Tooltip for delete button (simple hover effect)
        delete_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Delete entry"))
        delete_btn.bind("<Leave>", self._hide_tooltip)
    
    def _on_delete_click(self):
        """Handle delete button click."""
        self.controller.delete_screenshot(self.meta)
    
    def _show_tooltip(self, event, text):
        """Show a simple tooltip."""
        # For now, just change the cursor to indicate action
        event.widget.configure(cursor="hand2")
    
    def _hide_tooltip(self, event):
        """Hide tooltip."""
        event.widget.configure(cursor="")
    
    def _setup_drag_and_drop(self, row: ctk.CTkFrame):
        """Setup drag and drop functionality for reordering."""
        # Store original position for live dragging
        self._original_y = 0
        self._drag_offset = 0
        
        # Make the frame draggable, but only on empty areas
        row.bind("<Button-1>", self._start_drag)
        row.bind("<B1-Motion>", self._drag_motion)
        row.bind("<ButtonRelease-1>", self._end_drag)
        row.bind("<Enter>", self._on_enter)
        row.bind("<Leave>", self._on_leave)
        
        # Only bind to labels and frames, not input widgets
        for child in row.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                child.bind("<Button-1>", self._start_drag)
                child.bind("<B1-Motion>", self._drag_motion)
                child.bind("<ButtonRelease-1>", self._end_drag)
                child.bind("<Enter>", self._on_enter)
                child.bind("<Leave>", self._on_leave)
                # Bind to labels only, not input widgets
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ctk.CTkLabel):
                        grandchild.bind("<Button-1>", self._start_drag)
                        grandchild.bind("<B1-Motion>", self._drag_motion)
                        grandchild.bind("<ButtonRelease-1>", self._end_drag)
                        grandchild.bind("<Enter>", self._on_enter)
                        grandchild.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Show hand cursor when hovering over draggable areas."""
        event.widget.configure(cursor="hand2")
    
    def _on_leave(self, event):
        """Reset cursor when leaving draggable areas."""
        event.widget.configure(cursor="")
    
    def _start_drag(self, event):
        """Start dragging operation."""
        self._drag_start_y = event.y_root
        self._original_y = self.meta.entry_frame.winfo_y()
        self._dragging = True
        
        # Visual feedback - change appearance and raise the frame
        self.meta.entry_frame.configure(fg_color=("gray75", "gray25"))
        self.meta.entry_frame.lift()  # Bring to front
        
        # Change cursor to indicate dragging
        event.widget.configure(cursor="fleur")
    
    def _drag_motion(self, event):
        """Handle drag motion with live movement."""
        if hasattr(self, '_dragging') and self._dragging:
            # Calculate drag offset
            current_drag_distance = event.y_root - self._drag_start_y
            
            # Store current offset for end_drag calculation
            self._drag_offset = current_drag_distance
            
            # Visual feedback without breaking the layout
            # Just change the border or shadow to show movement direction
            if abs(current_drag_distance) > 20:
                if current_drag_distance > 0:
                    # Dragging down - add bottom border effect
                    self.meta.entry_frame.configure(border_width=2, border_color="blue")
                else:
                    # Dragging up - add top border effect  
                    self.meta.entry_frame.configure(border_width=2, border_color="green")
            else:
                # Reset border when not dragging far enough
                self.meta.entry_frame.configure(border_width=0)
    
    def _end_drag(self, event):
        """End dragging operation."""
        if hasattr(self, '_dragging') and self._dragging:
            self._dragging = False
            
            # Reset visual feedback
            self.meta.entry_frame.configure(
                fg_color=("gray90", "gray20"),
                border_width=0
            )
            event.widget.configure(cursor="hand2")  # Back to hand cursor
            
            # Calculate if we should reorder based on total drag distance
            if hasattr(self, '_drag_offset') and abs(self._drag_offset) > 50:  # Minimum drag distance for reorder
                self.controller.reorder_entry(self.meta, self._drag_offset > 0)
    
    def _validate_caption_field(self, *args):
        """Validate the caption field."""
        if self.meta.caption.get().strip():
            self.caption_entry.configure(border_color=("gray", "gray"))
        else:
            self.caption_entry.configure(border_color=("red", "red"))
    
    def _validate_what_field(self, *args):
        """Validate the what field."""
        if self.meta.what.get().strip():
            self.what_entry.configure(border_color=("gray", "gray"))
        else:
            self.what_entry.configure(border_color=("red", "red"))
    
    def _on_field_change(self, *args):
        """Handle field change to trigger auto-save."""
        # Trigger auto-save with a small delay to avoid too frequent saves
        if hasattr(self.controller, '_save_session_data'):
            self.controller.root.after(2000, self.controller._save_session_data)
    
    def _on_branch_change(self, *args):
        """Handle branch selection change."""
        self._on_field_change()


class ImageViewerDialog:
    """Modal dialog for viewing full-size images."""
    
    @staticmethod
    def show_image(parent: ctk.CTk, image_path: Path):
        """Display the image in a modal dialog."""
        dialog = ctk.CTkToplevel(parent)
        dialog.title(image_path.name)
        dialog.transient(parent)
        dialog.grab_set()
        
        try:
            img = Image.open(image_path)
        except Exception as e:
            ctk.CTkLabel(dialog, text=f"Error opening image: {e}").pack(padx=20, pady=20)
            return
        
        # Scale image to fit screen
        max_width = parent.winfo_screenwidth() - 100
        max_height = parent.winfo_screenheight() - 150
        
        w, h = img.size
        scale = min(1, max_width / w, max_height / h)
        
        if scale < 1:
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)
        
        # Create CTkImage and display
        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        label = ctk.CTkLabel(dialog, image=ctk_image, text="")
        label.pack(padx=10, pady=10)
        
        # Center the dialog
        dialog.geometry(f"{img.size[0] + 20}x{img.size[1] + 20}")
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")


class ExportSuccessDialog:
    """Dialog for showing export success with file navigation options."""
    
    @staticmethod
    def _load_icon_for_dialog(icon_name: str, size: tuple = (20, 20)) -> ctk.CTkImage:
        """Load an icon for use in dialog buttons."""
        try:
            icon_path = get_icon_path(icon_name)
            if icon_path.exists():
                img = Image.open(icon_path)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception:
            pass
        return None
    
    @staticmethod
    def show_success(parent: ctk.CTk, file_path: Path):
        """Display export success dialog with navigation options."""
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Export Complete")
        dialog.geometry("400x200")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Success message
        ctk.CTkLabel(
            dialog, 
            text="✅ Export Complete!",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            dialog, 
            text=f"Document saved as:\n{file_path.name}",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(0, 20))
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Open folder button
        folder_icon = ExportSuccessDialog._load_icon_for_dialog("folder.png", (20, 20))
        ctk.CTkButton(
            button_frame,
            text="Open Folder" if folder_icon else "📁 Open Folder",
            image=folder_icon,
            command=lambda: ExportSuccessDialog._open_folder(file_path),
            width=120,
            height=35
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Open document button
        export_icon = ExportSuccessDialog._load_icon_for_dialog("export.png", (20, 20))
        ctk.CTkButton(
            button_frame,
            text="Open Document" if export_icon else "📄 Open Document",
            image=export_icon,
            command=lambda: ExportSuccessDialog._open_document(file_path),
            width=120,
            height=35
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Close button
        ctk.CTkButton(
            button_frame,
            text="Close",
            command=dialog.destroy,
            width=80,
            height=35,
            fg_color="gray",
            hover_color="darkgray"
        ).pack(side=tk.RIGHT)
    
    @staticmethod
    def _open_folder(file_path: Path):
        """Open the folder containing the exported file."""
        try:
            folder_path = file_path.parent
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', folder_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
    
    @staticmethod
    def _open_document(file_path: Path):
        """Open the exported document with the default application."""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open document: {e}")
