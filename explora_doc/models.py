"""Data models for ExploraDoc application."""

from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk
import customtkinter as ctk


@dataclass
class ScreenshotMeta:
    """Metadata and UI references for a screenshot entry."""
    path: Path
    what: tk.StringVar = field(default_factory=tk.StringVar)
    branch: tk.StringVar = field(default_factory=lambda: tk.StringVar(value="dev"))
    caption: tk.StringVar = field(default_factory=tk.StringVar)
    # UI widget references
    entry_frame: ctk.CTkFrame = None  # will be set after widget creation
