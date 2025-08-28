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
    caption: tk.StringVar = field(default_factory=tk.StringVar)
    # UI widget references
    entry_frame: ctk.CTkFrame = None  # will be set after widget creation


@dataclass
class TestingCharter:
    """Testing charter data model."""
    objective: tk.StringVar = field(default_factory=tk.StringVar)
    whats_checked: tk.StringVar = field(default_factory=tk.StringVar)  # Bullet points
    prerequisites: tk.StringVar = field(default_factory=tk.StringVar)
    exclusions: tk.StringVar = field(default_factory=tk.StringVar)
    defects: tk.StringVar = field(default_factory=tk.StringVar)
    peer_review: tk.StringVar = field(default_factory=tk.StringVar)
    enabled: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=False))
