"""Image annotation editor with drawing tools for ExploraDoc."""

import copy
import math
import os
import shutil
import tempfile
import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union
from unittest import result
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont


class ToolType(Enum):
    """Available annotation tools."""
    NONE = "none"
    RECT = "rectangle"
    ELLIPSE = "ellipse"
    TEXT = "text"
    HIGHLIGHT = "highlight"


@dataclass
class BaseAnnotation:
    """Base annotation with unique ID and type."""
    id: int
    kind: ToolType


@dataclass
class RectAnnotation(BaseAnnotation):
    """Rectangle annotation."""
    x0: int
    y0: int
    x1: int
    y1: int
    outline: str
    width: int
    fill: Optional[str] = None


@dataclass
class EllipseAnnotation(BaseAnnotation):
    """Ellipse annotation."""
    x0: int
    y0: int
    x1: int
    y1: int
    outline: str
    width: int
    fill: Optional[str] = None


@dataclass
class TextAnnotation(BaseAnnotation):
    """Text annotation."""
    x: int
    y: int
    text: str
    font_name: str
    font_size: int
    fill: str


@dataclass
class HighlightAnnotation(BaseAnnotation):
    """Highlight line annotation with snapped angles."""
    x0: int
    y0: int
    x1: int
    y1: int
    color: str
    width: int
    alpha: int


class UndoRedoManager:
    """Manages undo/redo operations using state snapshots."""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.undo_stack: List[List[BaseAnnotation]] = []
        self.redo_stack: List[List[BaseAnnotation]] = []

    def push_state(self, annotations: List[BaseAnnotation]) -> None:
        state = copy.deepcopy(annotations)
        self.undo_stack.append(state)
        self.redo_stack.clear()
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def undo(self) -> Optional[List[BaseAnnotation]]:
        if not self.undo_stack:
            return None
        current_state = self.undo_stack.pop()
        self.redo_stack.append(current_state)
        return copy.deepcopy(self.undo_stack[-1]) if self.undo_stack else []

    def redo(self) -> Optional[List[BaseAnnotation]]:
        if not self.redo_stack:
            return None
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        return copy.deepcopy(state)

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

class AnnotationRenderer:
    """Handles rendering annotations on both Canvas and Pillow ImageDraw."""
    @staticmethod
    def render_to_canvas(canvas: tk.Canvas, annotation: BaseAnnotation, scale_factor: float = 1.0) -> List[int]:
        items = []
        if isinstance(annotation, RectAnnotation):
            x0, y0 = annotation.x0 * scale_factor, annotation.y0 * scale_factor
            x1, y1 = annotation.x1 * scale_factor, annotation.y1 * scale_factor
            items.append(canvas.create_rectangle(
                x0, y0, x1, y1,
                outline=annotation.outline,
                width=annotation.width,
                fill=annotation.fill if annotation.fill else ""
            ))
        elif isinstance(annotation, EllipseAnnotation):
            x0, y0 = annotation.x0 * scale_factor, annotation.y0 * scale_factor
            x1, y1 = annotation.x1 * scale_factor, annotation.y1 * scale_factor
            items.append(canvas.create_oval(
                x0, y0, x1, y1,
                outline=annotation.outline,
                width=annotation.width,
                fill=annotation.fill if annotation.fill else ""
            ))
        elif isinstance(annotation, TextAnnotation):
            x, y = annotation.x * scale_factor, annotation.y * scale_factor
            items.append(canvas.create_text(
                x, y,
                text=annotation.text,
                fill=annotation.fill,
                font=(annotation.font_name, int(annotation.font_size * scale_factor)),
                anchor="nw"
            ))
        elif isinstance(annotation, HighlightAnnotation):
            return items
        return items

    @staticmethod
    def render_to_pillow(draw: ImageDraw.ImageDraw, annotation: BaseAnnotation) -> None:
        if isinstance(annotation, RectAnnotation):
            bbox = (annotation.x0, annotation.y0, annotation.x1, annotation.y1)
            draw.rectangle(bbox, outline=annotation.outline, width=annotation.width, fill=annotation.fill)
        elif isinstance(annotation, EllipseAnnotation):
            bbox = (annotation.x0, annotation.y0, annotation.x1, annotation.y1)
            draw.ellipse(bbox, outline=annotation.outline, width=annotation.width, fill=annotation.fill)
        elif isinstance(annotation, TextAnnotation):
            try:
                font = ImageFont.truetype("arial.ttf", annotation.font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
            draw.text((annotation.x, annotation.y), annotation.text, fill=annotation.fill, font=font)
        elif isinstance(annotation, HighlightAnnotation):
            return

class ImageAnnotationEditor:
    @staticmethod
    def render_to_canvas(canvas: tk.Canvas, annotation: BaseAnnotation, 
                        scale_factor: float = 1.0) -> List[int]:
        """Render annotation to Tkinter Canvas and return created item IDs."""
        items = []
        
        if isinstance(annotation, RectAnnotation):
            x0, y0 = annotation.x0 * scale_factor, annotation.y0 * scale_factor
            x1, y1 = annotation.x1 * scale_factor, annotation.y1 * scale_factor
            
            if annotation.fill:
                items.append(canvas.create_rectangle(
                    x0, y0, x1, y1, 
                    outline=annotation.outline, 
                    width=annotation.width,
                    fill=annotation.fill
                ))
            else:
                items.append(canvas.create_rectangle(
                    x0, y0, x1, y1, 
                    outline=annotation.outline, 
                    width=annotation.width,
                    fill=""
                ))
        
        elif isinstance(annotation, EllipseAnnotation):
            x0, y0 = annotation.x0 * scale_factor, annotation.y0 * scale_factor
            x1, y1 = annotation.x1 * scale_factor, annotation.y1 * scale_factor
            
            if annotation.fill:
                items.append(canvas.create_oval(
                    x0, y0, x1, y1, 
                    outline=annotation.outline, 
                    width=annotation.width,
                    fill=annotation.fill
                ))
            else:
                items.append(canvas.create_oval(
                    x0, y0, x1, y1, 
                    outline=annotation.outline, 
                    width=annotation.width,
                    fill=""
                ))
        
        elif isinstance(annotation, TextAnnotation):
            x, y = annotation.x * scale_factor, annotation.y * scale_factor
            items.append(canvas.create_text(
                x, y,
                text=annotation.text,
                fill=annotation.fill,
                font=(annotation.font_name, int(annotation.font_size * scale_factor)),
                anchor="nw"
            ))
        
        elif isinstance(annotation, HighlightAnnotation):
            # Skip direct canvas drawing; handled by RGBA overlay image
            return items
        
        return items
    
    @staticmethod
    def render_to_pillow(draw: ImageDraw.ImageDraw, annotation: BaseAnnotation) -> None:
        """Render annotation to Pillow ImageDraw."""
        if isinstance(annotation, RectAnnotation):
            bbox = (annotation.x0, annotation.y0, annotation.x1, annotation.y1)
            if annotation.fill:
                draw.rectangle(bbox, outline=annotation.outline, 
                             width=annotation.width, fill=annotation.fill)
            else:
                draw.rectangle(bbox, outline=annotation.outline, 
                             width=annotation.width)
        
        elif isinstance(annotation, EllipseAnnotation):
            bbox = (annotation.x0, annotation.y0, annotation.x1, annotation.y1)
            if annotation.fill:
                draw.ellipse(bbox, outline=annotation.outline, 
                           width=annotation.width, fill=annotation.fill)
            else:
                draw.ellipse(bbox, outline=annotation.outline, 
                           width=annotation.width)
        
        elif isinstance(annotation, TextAnnotation):
            try:
                # Try to load a system font
                font = ImageFont.truetype("arial.ttf", annotation.font_size)
            except (OSError, IOError):
                try:
                    # Fallback to default font
                    font = ImageFont.load_default()
                except:
                    font = None
            
            draw.text((annotation.x, annotation.y), annotation.text, 
                     fill=annotation.fill, font=font)
        
        elif isinstance(annotation, HighlightAnnotation):
            # Skip here; real alpha rendering handled in _composite_and_save
            return
    
    @staticmethod
    def _lighten_color(hex_color: str, factor: float = 0.5) -> str:
        """Lighten a hex color by mixing with white."""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Mix with white
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _alpha_to_stipple(alpha: int) -> Optional[str]:
        """Map an alpha value (0-255) to a Tk stipple pattern to simulate transparency.
        Tk canvas does not support real per-pixel alpha for vector shapes, so we
        approximate: lower alpha -> sparser stipple pattern.
        """
        if alpha <= 64:
            return 'gray25'
        if alpha <= 128:
            return 'gray50'
        if alpha <= 192:
            return 'gray75'
        return None


class AnnotationRenderer:
    """Handles rendering annotations on both Canvas and Pillow ImageDraw."""
    
    @staticmethod
    def render_to_canvas(canvas: tk.Canvas, annotation: BaseAnnotation, 
                        scale_factor: float = 1.0) -> List[int]:
        """Render annotation to Tkinter Canvas and return created item IDs."""
        items = []
        if isinstance(annotation, RectAnnotation):
            x0, y0 = annotation.x0 * scale_factor, annotation.y0 * scale_factor
            x1, y1 = annotation.x1 * scale_factor, annotation.y1 * scale_factor
            if annotation.fill:
                items.append(canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline=annotation.outline,
                    width=annotation.width,
                    fill=annotation.fill
                ))
            else:
                items.append(canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline=annotation.outline,
                    width=annotation.width,
                    fill=""
                ))
        elif isinstance(annotation, EllipseAnnotation):
            x0, y0 = annotation.x0 * scale_factor, annotation.y0 * scale_factor
            x1, y1 = annotation.x1 * scale_factor, annotation.y1 * scale_factor
            if annotation.fill:
                items.append(canvas.create_oval(
                    x0, y0, x1, y1,
                    outline=annotation.outline,
                    width=annotation.width,
                    fill=annotation.fill
                ))
            else:
                items.append(canvas.create_oval(
                    x0, y0, x1, y1,
                    outline=annotation.outline,
                    width=annotation.width,
                    fill=""
                ))
        elif isinstance(annotation, TextAnnotation):
            x, y = annotation.x * scale_factor, annotation.y * scale_factor
            items.append(canvas.create_text(
                x, y,
                text=annotation.text,
                fill=annotation.fill,
                font=(annotation.font_name, int(annotation.font_size * scale_factor)),
                anchor="nw"
            ))
        elif isinstance(annotation, HighlightAnnotation):
            return items
        return items

    @staticmethod
    def render_to_pillow(draw: ImageDraw.ImageDraw, annotation: BaseAnnotation) -> None:
        if isinstance(annotation, RectAnnotation):
            bbox = (annotation.x0, annotation.y0, annotation.x1, annotation.y1)
            if annotation.fill:
                draw.rectangle(bbox, outline=annotation.outline,
                               width=annotation.width, fill=annotation.fill)
            else:
                draw.rectangle(bbox, outline=annotation.outline,
                               width=annotation.width)
        elif isinstance(annotation, EllipseAnnotation):
            bbox = (annotation.x0, annotation.y0, annotation.x1, annotation.y1)
            if annotation.fill:
                draw.ellipse(bbox, outline=annotation.outline,
                             width=annotation.width, fill=annotation.fill)
            else:
                draw.ellipse(bbox, outline=annotation.outline,
                             width=annotation.width)
        elif isinstance(annotation, TextAnnotation):
            try:
                font = ImageFont.truetype("arial.ttf", annotation.font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
            draw.text((annotation.x, annotation.y), annotation.text,
                      fill=annotation.fill, font=font)
        elif isinstance(annotation, HighlightAnnotation):
            return

    @staticmethod
    def _lighten_color(hex_color: str, factor: float = 0.5) -> str:
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _alpha_to_stipple(alpha: int) -> Optional[str]:
        if alpha <= 64:
            return 'gray25'
        if alpha <= 128:
            return 'gray50'
        if alpha <= 192:
            return 'gray75'
        return None

class ImageAnnotationEditor:
    """Modal image annotation editor with drawing tools."""

    def __init__(self, parent: ctk.CTk, image_path: Path,
                 on_save_callback: Callable[[Path], None] = None):
        # Basic refs
        self.parent = parent
        self.image_path = image_path
        self.on_save_callback = on_save_callback

        # Annotation state
        self.annotations = []
        self.undo_manager = UndoRedoManager()
        self.current_tool = ToolType.RECT
        self.next_annotation_id = 1

        # Drawing runtime state
        self.is_drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_item_id = None
        self.text_entry_widget = None

        # Image / display
        self.original_image = None
        self.display_image = None
        self.scale_factor = 1.0
        self.canvas_image_id = None
        self.highlight_overlay_id = None
        self.highlight_overlay_photo = None  # keep PhotoImage reference

        # Style defaults
        self.stroke_color = "#ff0000"
        self.fill_color = None
        self.stroke_width = 2
        self.text_size = 16
        self.text_color = "#000000"
        self.highlight_color = "#ffff00"
        self.highlight_alpha = 64  # ~25% opacity

        # UI handles
        self.window = None
        self.canvas = None
        self.toolbar_frame = None
        self.tool_buttons = {}
        self.undo_btn = None
        self.redo_btn = None

        # Build UI
        self._load_image()
        self._build_ui()
        self._bind_events()
    
    def _load_image(self) -> None:
        """Load and prepare the image for editing."""
        try:
            self.original_image = Image.open(self.image_path)
            # Convert to RGBA for consistent handling
            if self.original_image.mode != 'RGBA':
                self.original_image = self.original_image.convert('RGBA')
            
            # Calculate scale factor to fit on screen
            screen_width = self.parent.winfo_screenwidth() - 200
            screen_height = self.parent.winfo_screenheight() - 300
            
            img_width, img_height = self.original_image.size
            scale_x = screen_width / img_width
            scale_y = screen_height / img_height
            self.scale_factor = min(1.0, scale_x, scale_y)
            
            # Create display image
            if self.scale_factor < 1.0:
                new_size = (int(img_width * self.scale_factor), 
                           int(img_height * self.scale_factor))
                self.display_image = self.original_image.resize(new_size, Image.LANCZOS)
            else:
                self.display_image = self.original_image.copy()
                
        except Exception as e:
            raise Exception(f"Failed to load image: {e}")
    
    def _build_ui(self) -> None:
        """Build the annotation editor UI."""
        # Create modal window
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title(f"Annotate - {self.image_path.name}")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Configure window
        canvas_width = self.display_image.size[0] + 20
        canvas_height = self.display_image.size[1] + 20
        toolbar_height = 60
        
        window_width = canvas_width + 20
        window_height = canvas_height + toolbar_height + 40
        
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.resizable(False, False)
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (window_width // 2)
        y = (self.window.winfo_screenheight() // 2) - (window_height // 2)
        self.window.geometry(f"+{x}+{y}")
        
        self._create_toolbar()
        self._create_canvas()
        self._update_button_states()
    
    def _create_toolbar(self) -> None:
        """Create the toolbar with tools and controls."""
        self.toolbar_frame = ctk.CTkFrame(self.window)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)
        
        # Tool buttons with better styling
        tools_frame = ctk.CTkFrame(self.toolbar_frame)
        tools_frame.pack(side=tk.LEFT, padx=(0, 6))
        
        ctk.CTkLabel(tools_frame, text="Tools:", font=ctk.CTkFont(size=11, weight="bold")).pack(side=tk.LEFT, padx=(6, 4))
        
        tool_configs = [
            (ToolType.RECT, "Rectangle", "Draw rectangles"),
            (ToolType.ELLIPSE, "Circle", "Draw circles/ellipses"),
            (ToolType.TEXT, "Text", "Add text"),
            (ToolType.HIGHLIGHT, "Highlight", "Draw highlight lines"),
        ]
        
        for tool_type, label, tooltip in tool_configs:
            btn = ctk.CTkButton(
                tools_frame,
                text=label,
                width=70,
                height=28,
                command=lambda t=tool_type: self._set_tool(t),
                font=ctk.CTkFont(size=10),
                corner_radius=4
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.tool_buttons[tool_type] = btn
        
        # Color picker with better layout
        color_frame = ctk.CTkFrame(self.toolbar_frame)
        color_frame.pack(side=tk.LEFT, padx=(0, 6))
        
        ctk.CTkLabel(color_frame, text="Color:", font=ctk.CTkFont(size=11, weight="bold")).pack(side=tk.TOP, padx=4, pady=(4, 1))
        
        # Color buttons in a cleaner grid
        color_container = ctk.CTkFrame(color_frame)
        color_container.pack(padx=4, pady=(0, 4))
        
        colors = [
            ("#ff0000", "Red"), ("#00ff00", "Green"), ("#0000ff", "Blue"),
            ("#ffff00", "Yellow"), ("#ff00ff", "Magenta"), ("#000000", "Black")
        ]
        
        for i, (color, name) in enumerate(colors):
            row = i // 3
            col = i % 3
            color_btn = ctk.CTkButton(
                color_container,
                text="",
                width=20,
                height=20,
                fg_color=color,
                hover_color=color,
                border_width=1,
                border_color="white",
                command=lambda c=color: self._set_color(c),
                corner_radius=3
            )
            color_btn.grid(row=row, column=col, padx=1, pady=1)

        # Text size selector
        text_frame = ctk.CTkFrame(self.toolbar_frame)
        text_frame.pack(side=tk.LEFT, padx=(0, 6))
        ctk.CTkLabel(text_frame, text="Text Size:", font=ctk.CTkFont(size=11, weight="bold")).pack(side=tk.TOP, padx=4, pady=(4, 1))
        text_sizes = [10, 12, 14, 16, 18, 20, 24, 28, 32]
        self.text_size_var = tk.StringVar(value=str(self.text_size))
        text_menu = ctk.CTkOptionMenu(text_frame,
                                      variable=self.text_size_var,
                                      values=[str(s) for s in text_sizes],
                                      command=lambda v: self._set_text_size(int(v)),
                                      width=60,
                                      height=24)
        text_menu.pack(padx=4, pady=(0,4))
        
        # Undo/Redo with better styling
        action_frame = ctk.CTkFrame(self.toolbar_frame)
        action_frame.pack(side=tk.LEFT, padx=(0, 6))
        
        ctk.CTkLabel(action_frame, text="Actions:", font=ctk.CTkFont(size=11, weight="bold")).pack(side=tk.LEFT, padx=(6, 4))
        
        self.undo_btn = ctk.CTkButton(
            action_frame,
            text="Undo",
            width=50,
            height=28,
            command=self._undo,
            font=ctk.CTkFont(size=10),
            corner_radius=4
        )
        self.undo_btn.pack(side=tk.LEFT, padx=1)
        
        self.redo_btn = ctk.CTkButton(
            action_frame,
            text="Redo",
            width=50,
            height=28,
            command=self._redo,
            font=ctk.CTkFont(size=10),
            corner_radius=4
        )
        self.redo_btn.pack(side=tk.LEFT, padx=1)
        
        # Done/Cancel buttons with better colors
        control_frame = ctk.CTkFrame(self.toolbar_frame)
        control_frame.pack(side=tk.RIGHT)
        
        cancel_btn = ctk.CTkButton(
            control_frame,
            text="Cancel",
            width=65,
            height=32,
            command=self._cancel,
            fg_color=("#d32f2f", "#f44336"),
            hover_color=("#c62828", "#e53935"),
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6
        )
        cancel_btn.pack(side=tk.LEFT, padx=3)
        
        done_btn = ctk.CTkButton(
            control_frame,
            text="Done",
            width=65,
            height=32,
            command=self._done,
            fg_color=("#2e7d32", "#4caf50"),
            hover_color=("#1b5e20", "#43a047"),
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6
        )
        done_btn.pack(side=tk.LEFT, padx=3)
    
    def _create_canvas(self) -> None:
        """Create the main canvas for image and annotations."""
        canvas_frame = ctk.CTkFrame(self.window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.display_image.size[0],
            height=self.display_image.size[1],
            bg="white",
            highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=10)
        
        # Load image onto canvas
        from PIL import ImageTk
        self.photo = ImageTk.PhotoImage(self.display_image)
        self.canvas_image_id = self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self.photo
        )
    
    def _bind_events(self) -> None:
        """Bind mouse events for drawing."""
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self._refresh_highlight_overlay()

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    def _draw_highlight_polygon(self, draw_ctx: ImageDraw.ImageDraw, ann: HighlightAnnotation) -> None:
        scale = 1.0  # annotation coords already in image space
        x0 = ann.x0
        y0 = ann.y0
        x1 = ann.x1
        y1 = ann.y1
        dx = x1 - x0
        dy = y1 - y0
        length = math.sqrt(dx*dx + dy*dy)
        r, g, b = self._hex_to_rgb(ann.color)
        color = (r, g, b, ann.alpha)
        if length > 0:
            perp_x = -dy / length * (ann.width / 2)
            perp_y = dx / length * (ann.width / 2)
            points = [
                (x0 + perp_x, y0 + perp_y),
                (x1 + perp_x, y1 + perp_y),
                (x1 - perp_x, y1 - perp_y),
                (x0 - perp_x, y0 - perp_y)
            ]
            draw_ctx.polygon(points, fill=color)
            draw_ctx.ellipse([x0 - ann.width/2, y0 - ann.width/2, x0 + ann.width/2, y0 + ann.width/2], fill=color)
            draw_ctx.ellipse([x1 - ann.width/2, y1 - ann.width/2, x1 + ann.width/2, y1 + ann.width/2], fill=color)
        else:
            draw_ctx.ellipse([x0 - ann.width/2, y0 - ann.width/2, x0 + ann.width/2, y0 + ann.width/2], fill=color)

    def _refresh_highlight_overlay(self, temp: Optional[HighlightAnnotation] = None) -> None:
        if not self.original_image or not self.canvas:
            return
        # Local import to avoid global dependency if ImageTk not yet loaded elsewhere
        from PIL import ImageTk
        # Base overlay in display size
        overlay = Image.new('RGBA', self.original_image.size, (0, 0, 0, 0))
        draw_ctx = ImageDraw.Draw(overlay)
        for ann in self.annotations:
            if isinstance(ann, HighlightAnnotation):
                self._draw_highlight_polygon(draw_ctx, ann)
        if temp:
            self._draw_highlight_polygon(draw_ctx, temp)
        # Scale overlay if needed for display
        if self.scale_factor != 1.0:
            disp_overlay = overlay.resize(self.display_image.size, Image.LANCZOS)
        else:
            disp_overlay = overlay
        self.highlight_overlay_photo = ImageTk.PhotoImage(disp_overlay)
        if self.highlight_overlay_id is None:
            self.highlight_overlay_id = self.canvas.create_image(0, 0, anchor='nw', image=self.highlight_overlay_photo)
        else:
            self.canvas.itemconfigure(self.highlight_overlay_id, image=self.highlight_overlay_photo)
        # Keep overlay just above base image
        if self.canvas_image_id is not None and self.highlight_overlay_id is not None:
            self.canvas.tag_raise(self.highlight_overlay_id, self.canvas_image_id)
    
    def _set_tool(self, tool: ToolType) -> None:
        """Set the current drawing tool."""
        self.current_tool = tool
        
        # Update button appearances with better visual feedback
        for tool_type, btn in self.tool_buttons.items():
            if tool_type == tool:
                # Selected tool - highlighted appearance
                btn.configure(
                    fg_color=("#1f538d", "#14375e"),
                    hover_color=("#1e88e5", "#1976d2"),
                    text_color=("white", "white")
                )
            else:
                # Unselected tool - normal appearance
                btn.configure(
                    fg_color=("gray75", "gray25"),
                    hover_color=("gray65", "gray35"),
                    text_color=("black", "white")
                )
    
    def _set_color(self, color: str) -> None:
        """Set the current stroke/text color."""
        self.stroke_color = color
        self.text_color = color
        # Also update highlight color so chosen palette applies to highlighter
        self.highlight_color = color
        # If currently using highlight tool, refresh overlay preview (no temp)
        if self.current_tool == ToolType.HIGHLIGHT:
            self._refresh_highlight_overlay()

    def _set_text_size(self, size: int) -> None:
        """Update text size for new text annotations and active entry widget."""
        self.text_size = size
        # Update active entry widget font if currently typing
        if self.text_entry_widget is not None:
            try:
                self.text_entry_widget.configure(font=ctk.CTkFont(size=self.text_size))
            except Exception:
                pass
    
    def _on_mouse_down(self, event) -> None:
        """Handle mouse button press."""
        if self.current_tool == ToolType.TEXT:
            self._start_text_entry(event.x, event.y)
        elif self.current_tool in [ToolType.RECT, ToolType.ELLIPSE, ToolType.HIGHLIGHT]:
            self.is_drawing = True
            self.start_x = event.x
            self.start_y = event.y
            if self.current_tool == ToolType.HIGHLIGHT:
                self._refresh_highlight_overlay()  # clear temp
    
    def _on_mouse_move(self, event) -> None:
        """Handle mouse movement during drawing."""
        if not self.is_drawing:
            return
        
        # Remove previous preview
        if self.current_item_id:
            self.canvas.delete(self.current_item_id)
            self.current_item_id = None
        
        current_x, current_y = event.x, event.y
        
        if self.current_tool == ToolType.RECT:
            self.current_item_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, current_x, current_y,
                outline=self.stroke_color, width=self.stroke_width, fill=""
            )
        elif self.current_tool == ToolType.ELLIPSE:
            self.current_item_id = self.canvas.create_oval(
                self.start_x, self.start_y, current_x, current_y,
                outline=self.stroke_color, width=self.stroke_width, fill=""
            )
        elif self.current_tool == ToolType.HIGHLIGHT:
            snapped_x, snapped_y = self._snap_highlight_line(
                self.start_x, self.start_y, current_x, current_y
            )
            temp = HighlightAnnotation(
                id=-1,
                kind=ToolType.HIGHLIGHT,
                x0=int(self.start_x / self.scale_factor),
                y0=int(self.start_y / self.scale_factor),
                x1=int(snapped_x / self.scale_factor),
                y1=int(snapped_y / self.scale_factor),
                color=self.highlight_color,
                width=12,
                alpha=self.highlight_alpha
            )
            self._refresh_highlight_overlay(temp=temp)
        
    
    def _on_mouse_up(self, event) -> None:
        """Handle mouse button release."""
        if not self.is_drawing:
            return
        
        self.is_drawing = False
        
        # Remove preview
        if self.current_item_id:
            self.canvas.delete(self.current_item_id)
            self.current_item_id = None
        
        current_x, current_y = event.x, event.y
        
        # Convert canvas coordinates to image coordinates
        img_start_x = int(self.start_x / self.scale_factor)
        img_start_y = int(self.start_y / self.scale_factor)
        img_end_x = int(current_x / self.scale_factor)
        img_end_y = int(current_y / self.scale_factor)
        
        # Create annotation
        if self.current_tool == ToolType.RECT:
            # Ensure proper ordering of coordinates
            x0, x1 = min(img_start_x, img_end_x), max(img_start_x, img_end_x)
            y0, y1 = min(img_start_y, img_end_y), max(img_start_y, img_end_y)
            
            annotation = RectAnnotation(
                id=self.next_annotation_id,
                kind=ToolType.RECT,
                x0=x0, y0=y0, x1=x1, y1=y1,
                outline=self.stroke_color,
                width=self.stroke_width,
                fill=self.fill_color
            )
            self._add_annotation(annotation)
        
        elif self.current_tool == ToolType.ELLIPSE:
            # Ensure proper ordering of coordinates
            x0, x1 = min(img_start_x, img_end_x), max(img_start_x, img_end_x)
            y0, y1 = min(img_start_y, img_end_y), max(img_start_y, img_end_y)
            
            annotation = EllipseAnnotation(
                id=self.next_annotation_id,
                kind=ToolType.ELLIPSE,
                x0=x0, y0=y0, x1=x1, y1=y1,
                outline=self.stroke_color,
                width=self.stroke_width,
                fill=self.fill_color
            )
            self._add_annotation(annotation)
        
        elif self.current_tool == ToolType.HIGHLIGHT:
            # Snap the line and convert to image coordinates
            snapped_x, snapped_y = self._snap_highlight_line(
                self.start_x, self.start_y, current_x, current_y
            )
            
            img_snapped_x = int(snapped_x / self.scale_factor)
            img_snapped_y = int(snapped_y / self.scale_factor)
            
            annotation = HighlightAnnotation(
                id=self.next_annotation_id,
                kind=ToolType.HIGHLIGHT,
                x0=img_start_x, y0=img_start_y,
                x1=img_snapped_x, y1=img_snapped_y,
                color=self.highlight_color,
                width=18,
                # Match StackOverflow example: int(255 * 0.25) => 63; use 64 for even value
                alpha=self.highlight_alpha
            )
            self._add_annotation(annotation)
            # Refresh overlay after adding highlight
            self._refresh_highlight_overlay()
    
    def _snap_highlight_line(self, x0: int, y0: int, x1: int, y1: int) -> Tuple[int, int]:
        """Snap highlight line to nearest 0°, 45°, or 90° angle."""
        dx = x1 - x0
        dy = y1 - y0
        
        if abs(dy) < abs(dx) / 2:
            # Horizontal (0°)
            return x1, y0
        elif abs(dx) < abs(dy) / 2:
            # Vertical (90°)
            return x0, y1
        else:
            # Diagonal (45°)
            distance = max(abs(dx), abs(dy))
            sign_x = 1 if dx >= 0 else -1
            sign_y = 1 if dy >= 0 else -1
            return x0 + distance * sign_x, y0 + distance * sign_y
    
    def _start_text_entry(self, x: int, y: int) -> None:
        """Start text entry at the clicked position."""
        if self.text_entry_widget:
            self.text_entry_widget.destroy()
        
        # Create text entry widget with transparent background
        self.text_entry_widget = ctk.CTkEntry(
            self.canvas,
            width=220,
            height=max(24, self.text_size + 8),  # tighter height to reduce illusion
            placeholder_text="Enter text...",
            bg_color="transparent",
            font=ctk.CTkFont(size=self.text_size)
        )
        
        # Position the entry widget exactly at the click coordinates
        # Use create_window to embed the widget in the canvas at exact coordinates
        self.text_entry_widget.canvas_window = self.canvas.create_window(
            x, y, 
            window=self.text_entry_widget, 
            anchor="nw"
        )
        
        self.text_entry_widget.focus()
        
        # Store position for annotation creation (convert to image coordinates)
        self.text_entry_widget.text_x = int(x / self.scale_factor)
        self.text_entry_widget.text_y = int(y / self.scale_factor)
        
        # Bind events
        self.text_entry_widget.bind("<Return>", self._commit_text)
        self.text_entry_widget.bind("<Escape>", self._cancel_text)
        self.text_entry_widget.bind("<FocusOut>", self._cancel_text)
    
    def _commit_text(self, event=None) -> None:
        """Commit text entry as annotation."""
        if not self.text_entry_widget:
            return
        
        text = self.text_entry_widget.get().strip()
        if text:
            annotation = TextAnnotation(
                id=self.next_annotation_id,
                kind=ToolType.TEXT,
                x=self.text_entry_widget.text_x,
                y=self.text_entry_widget.text_y,
                text=text,
                font_name="Arial",
                # Store font size in image coordinate space so display render ( * scale_factor ) matches entry size
                font_size=int(self.text_size / self.scale_factor) if self.scale_factor != 1.0 else self.text_size,
                fill=self.text_color
            )
            self._add_annotation(annotation)
        
        # Clean up the text entry widget
        if hasattr(self.text_entry_widget, 'canvas_window'):
            self.canvas.delete(self.text_entry_widget.canvas_window)
        self.text_entry_widget.destroy()
        self.text_entry_widget = None
    
    def _cancel_text(self, event=None) -> None:
        """Cancel text entry."""
        if self.text_entry_widget:
            # Remove the canvas window if it was created
            if hasattr(self.text_entry_widget, 'canvas_window'):
                self.canvas.delete(self.text_entry_widget.canvas_window)
            self.text_entry_widget.destroy()
            self.text_entry_widget = None
    
    def _add_annotation(self, annotation: BaseAnnotation) -> None:
        """Add annotation and update display."""
        # Push current state to undo stack before adding
        self.undo_manager.push_state(self.annotations)
        
        self.annotations.append(annotation)
        self.next_annotation_id += 1
        
        self._render_canvas()
        self._update_button_states()
    
    def _render_canvas(self) -> None:
        """Re-render all annotations on the canvas."""
        # Clear existing annotation items (keep background image)
        protected = {self.canvas_image_id}
        if self.highlight_overlay_id is not None:
            protected.add(self.highlight_overlay_id)

        to_delete = [item for item in self.canvas.find_all() if item not in protected]
        for item in to_delete:
            self.canvas.delete(item)

        # If overlay id was deleted somehow, reset so it can be recreated
        existing = set(self.canvas.find_all())
        if self.highlight_overlay_id is not None and self.highlight_overlay_id not in existing:
            self.highlight_overlay_id = None

        # Render vector annotations (excluding highlights which are on overlay)
        for annotation in self.annotations:
            AnnotationRenderer.render_to_canvas(self.canvas, annotation, self.scale_factor)

        # Refresh overlay (no temp) to ensure highlights remain visible
        self._refresh_highlight_overlay()
    
    def _undo(self) -> None:
        """Undo last annotation."""
        previous_state = self.undo_manager.undo()
        if previous_state is not None:
            self.annotations = previous_state
            self._render_canvas()
            self._update_button_states()
    
    def _redo(self) -> None:
        """Redo last undone annotation."""
        next_state = self.undo_manager.redo()
        if next_state is not None:
            self.annotations = next_state
            self._render_canvas()
            self._update_button_states()
    
    def _update_button_states(self) -> None:
        """Update undo/redo button states."""
        if self.undo_btn:
            state = "normal" if self.undo_manager.can_undo() else "disabled"
            self.undo_btn.configure(state=state)
        
        if self.redo_btn:
            state = "normal" if self.undo_manager.can_redo() else "disabled"
            self.redo_btn.configure(state=state)
    
    def _composite_and_save(self) -> bool:
        """Composite annotations onto image and save."""
        if not self.annotations:
            # No annotations to save
            return True
        
        temp_file_path = None
        try:
            # Create a temporary file for editing
            temp_suffix = self.image_path.suffix
            with tempfile.NamedTemporaryFile(suffix=temp_suffix, delete=False) as temp_file:
                temp_file_path = Path(temp_file.name)
            
            # Copy original image to temporary file
            try:
                shutil.copy2(str(self.image_path), str(temp_file_path))
                print(f"Copied original image to temporary file: {temp_file_path}")
            except Exception as e:
                print(f"Failed to copy original image to temporary file: {e}")
                return False
            
            # Open the temporary file for processing
            try:
                with Image.open(str(temp_file_path)) as temp_image:
                    # Ensure original image is RGBA for compositing
                    if temp_image.mode != 'RGBA':
                        base_image = temp_image.convert('RGBA')
                    else:
                        base_image = temp_image.copy()
            except Exception as e:
                print(f"Failed to open temporary image file: {e}")
                return False
            
            # Create transparent overlay for all annotations
            overlay = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Separate highlights and regular annotations
            highlights = []
            regular_annotations = []
            
            for annotation in self.annotations:
                if isinstance(annotation, HighlightAnnotation):
                    highlights.append(annotation)
                else:
                    regular_annotations.append(annotation)
            
            # First, render highlights with proper alpha
            for highlight in highlights:
                # Convert hex color to RGB
                color = highlight.color
                if color.startswith('#'):
                    hex_color = color[1:]
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                else:
                    # Default yellow
                    r, g, b = 255, 255, 0
                
                # Create a separate overlay for this highlight, initialized to fully transparent version of the tint color
                # Following the pattern from the Pillow documentation and StackOverflow example
                tint_color = (r, g, b)
                highlight_overlay = Image.new('RGBA', base_image.size, tint_color + (0,))
                highlight_draw = ImageDraw.Draw(highlight_overlay)
                
                # Use the alpha value from the annotation for the drawing operations
                color_with_alpha = tint_color + (highlight.alpha,)
                
                # Draw highlight as a thick line using polygon
                x0, y0, x1, y1 = highlight.x0, highlight.y0, highlight.x1, highlight.y1
                
                # Calculate perpendicular offset for line width
                dx = x1 - x0
                dy = y1 - y0
                length = math.sqrt(dx * dx + dy * dy)
                
                if length > 0:
                    # Calculate perpendicular unit vector
                    perp_x = -dy / length * (highlight.width / 2)
                    perp_y = dx / length * (highlight.width / 2)
                    
                    # Create polygon points for the thick line
                    points = [
                        (x0 + perp_x, y0 + perp_y),
                        (x1 + perp_x, y1 + perp_y),
                        (x1 - perp_x, y1 - perp_y),
                        (x0 - perp_x, y0 - perp_y)
                    ]
                    
                    # Draw the highlight polygon
                    highlight_draw.polygon(points, fill=color_with_alpha)
                    
                    # Add rounded end caps for smoother appearance
                    highlight_draw.ellipse(
                        [x0 - highlight.width/2, y0 - highlight.width/2,
                         x0 + highlight.width/2, y0 + highlight.width/2],
                        fill=color_with_alpha
                    )
                    highlight_draw.ellipse(
                        [x1 - highlight.width/2, y1 - highlight.width/2,
                         x1 + highlight.width/2, y1 + highlight.width/2],
                        fill=color_with_alpha
                    )
                else:
                    # Single point - draw a circle
                    highlight_draw.ellipse(
                        [x0 - highlight.width/2, y0 - highlight.width/2,
                         x0 + highlight.width/2, y0 + highlight.width/2],
                        fill=color_with_alpha
                    )
                
                # Composite this highlight onto the base image
                base_image = Image.alpha_composite(base_image, highlight_overlay)
            
            # Now render regular annotations on the overlay
            for annotation in regular_annotations:
                AnnotationRenderer.render_to_pillow(overlay_draw, annotation)
            
            # Composite the regular annotations overlay onto the base image
            result = Image.alpha_composite(base_image, overlay)
            
            # Handle different output formats
            if self.image_path.suffix.lower() in ['.jpg', '.jpeg']:
                # Convert to RGB for JPEG
                result = result.convert('RGB')

            # Save the final annotated image
            try:
                # First try to save to the same directory as the original
                annotated_path = self.image_path.with_stem(self.image_path.stem + "_annotated")
                
                # Ensure the target directory exists
                annotated_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    result.save(str(annotated_path))
                    print(f"Image saved to {annotated_path}")
                    
                    # Update path so the callback gets the right file
                    self.image_path = annotated_path
                    return True
                except (PermissionError, OSError, FileNotFoundError) as e:
                    print(f"Failed to save image to {annotated_path}: {e}")
                    
                    # Fallback: Save to user's Pictures folder
                    pictures_dir = Path.home() / "Pictures" / "ExploraDoc_Annotations"
                    pictures_dir.mkdir(parents=True, exist_ok=True)
                    
                    fallback_path = pictures_dir / annotated_path.name
                    
                    # If file already exists, add a timestamp
                    if fallback_path.exists():
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        stem = annotated_path.stem
                        suffix = annotated_path.suffix
                        fallback_path = pictures_dir / f"{stem}_{timestamp}{suffix}"
                    
                    try:
                        result.save(str(fallback_path))
                        print(f"Image saved to fallback location: {fallback_path}")
                        
                        # Update path so the callback gets the right file
                        self.image_path = fallback_path
                        return True
                    except Exception as fallback_error:
                        print(f"Failed to save to fallback location {fallback_path}: {fallback_error}")
                        return False
                
            except Exception as e:
                print(f"Failed to save image to original path: {e}")
                return False
            
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Save Error", f"Failed to save annotated image: {e}")
            return False
        
        finally:
            # Clean up temporary file
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                    print(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    print(f"Failed to clean up temporary file: {e}")
    
    def _done(self) -> None:
        """Save annotations and close editor."""
        if self._composite_and_save():
            # Call the save callback to refresh UI
            if self.on_save_callback:
                self.on_save_callback(self.image_path)
            
            self.window.destroy()
    
    def _cancel(self) -> None:
        """Cancel editing without saving."""
        # Cancel any active text entry
        self._cancel_text()
        
        # Destroy window
        self.window.destroy()
    
    @classmethod
    def open(cls, parent: ctk.CTk, image_path: Path, 
             on_save_callback: Callable[[Path], None] = None) -> 'ImageAnnotationEditor':
        """Convenience method to open the annotation editor."""
        try:
            editor = cls(parent, image_path, on_save_callback)
            return editor
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Editor Error", f"Failed to open image editor: {e}")
            return None
      