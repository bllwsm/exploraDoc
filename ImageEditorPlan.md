# Image Annotation Editor Integration Plan

## Goal
Add a modal CustomTkinter + Canvas based image annotation editor to allow users to draw rectangles, circles, highlight lines (snapped 0°/45°/90°), and place text onto screenshots before finalizing. Provide undo/redo, non-destructive session editing (apply only on Done), overwrite original file, and update main UI preview.

---
## User Journey
### Before
1. User captures screenshot (handled by file monitor) → thumbnail appears in the feed.
2. Clicking the thumbnail opens a static viewer (`ImageViewerDialog`). No editing possible.

### After
1. Screenshot captured → thumbnail appears.
2. User clicks thumbnail → Annotation Editor modal opens (blocks main window):
   - Left/Top toolbar: tool buttons: Select/Pointer (future), Rectangle, Ellipse, Text, Highlighter, Undo, Redo, Color picker, Stroke width, Text size, Done, Cancel.
   - Central canvas shows current image; drawing previews appear during drag/move.
3. User performs annotation actions:
   - Drag to create rectangle/ellipse (outline + optional semi-transparent fill for highlight clarity).
   - Click to start highlight line → move mouse (line preview snaps to nearest of 0°, 45°, 90° relative to start) → release to finalize (semi-transparent yellow line with fixed thickness, maybe 12px default, RGBA (255,255,0,96)).
   - Text tool: click → popup entry inline (CTkEntry) to type; Enter to commit or ESC to cancel text insertion.
   - Undo/Redo updates stacks instantly; canvas re-renders.
4. User clicks Done → composite annotations onto the original image (Pillow) → save overwrite → close modal → main UI thumbnail + any full-size references refresh.
5. User clicks Cancel or closes window → discard transient annotations; no file changes; UI unchanged.

Edge: If file has been externally modified while editing, prompt to reload or force save.

---
## Architectural Overview

### New Module: `image_editor.py`
Responsibilities:
- Provide `ImageAnnotationEditor` class to open modal for a given image path.
- Manage annotation state, tool selection, undo/redo, rendering pipeline.

### Key Components
1. `ToolType` (Enum): RECT, ELLIPSE, TEXT, HIGHLIGHT, NONE.
2. Annotation Data Classes (immutable-ish records with id & params):
   - `BaseAnnotation(id, kind)`
   - `RectAnnotation(x0, y0, x1, y1, outline, width, fill=None)`
   - `EllipseAnnotation(...)` (same fields as Rect)
   - `TextAnnotation(x, y, text, font_name, font_size, fill)`
   - `HighlightAnnotation(x0, y0, x1, y1, color, width, alpha)` (will be rendered as semi-transparent polygon or thick line).
3. `UndoRedoManager`:
   - Stacks of actions (list of callables or state snapshots). Simpler: maintain two stacks of full annotation list snapshots (since expected small # of annotations) for clarity & reliability.
4. `AnnotationRenderer` (internal helper):
   - Methods to draw each annotation onto a Pillow `ImageDraw` (for final merge) and onto the Tk Canvas (for preview/live). For live interactive shapes (current drag), a temporary canvas item.
5. `ImageAnnotationEditor` main class:
   - `__init__(parent, image_path, on_save_callback)`.
   - Methods: `_build_ui()`, `_bind_events()`, `_set_tool(tool)`, `_on_mouse_down/move/up`, `_add_annotation()`, `_undo()`, `_redo()`, `_render_canvas()`, `_composite_and_save()`, `_cancel()`, `_load_image()`, `_refresh_thumbnail_callback()` (optional), `_snap_highlight(start, current)`.

### Rendering Strategy
- Base image displayed as a Canvas image item.
- Annotations drawn as separate Canvas items (store item ids on each annotation) OR re-render entire overlay layer: For simplicity & correctness across undo/redo, re-render entire overlay each change:
  1. Clear overlay group (track ids).
  2. Iterate annotations: create canvas primitives.
- During drag: show a transient shape (not yet committed) updated on motion.
- Text placement: create temporary Entry widget overlay; after commit, store annotation and re-render.

### Undo/Redo Strategy
- After each mutation (add, delete future, text commit), push a deep-copied list of annotations onto undo stack; clearing redo stack.
- Undo: pop current onto redo, restore previous.
- Redo: pop redo onto undo.

### Highlighter Tool Implementation
- User drags start → current.
- Compute dx, dy; compute angle via `atan2(dy, dx)` in degrees.
- Candidate angles = 0°, 45°, 90°, 135°, 180°; snap to whichever has minimal angular distance (mirror for negative slopes). For simplicity: consider absolute slopes; decide orientation:
  - If abs(dy) < abs(dx)/2 → horizontal (0°)
  - Else if abs(dx) < abs(dy)/2 → vertical (90°)
  - Else 45° (sign based on dx*dy).
- Adjust end point to preserve projected length along snapped direction.
- Represent highlight as a thick semi-transparent line: In Canvas, use `create_line` with stipple? (Tk doesn't support per-item alpha); Instead: draw polygon (simulate) or accept opaque with lighter color. For final composite, blend using Pillow with RGBA on separate layer then alpha_composite.
- Final merge: create RGBA overlay, draw a line (rectangle) with chosen color and alpha (e.g., color=(255,255,0,96)), then alpha_composite onto base.

### Text Editing
- Font: Use default system font or attempt to load a TTF (optional config later).
- Inline entry: place Entry at click coords; when user presses Enter → if not empty create TextAnnotation; ESC or focus out with empty discards.

### Saving (Done)
1. Open original with Pillow, ensure `convert("RGBA")` to composite.
2. Create transparent RGBA overlay same size.
3. For each annotation, draw onto overlay using `ImageDraw` primitives (rectangle, ellipse, text, highlight line -> `line` with width; optionally also draw semi-transparent fill for highlight only).
4. `Image.alpha_composite(base, overlay)`.
5. Convert back to original mode if desired (keep RGBA for PNG; if JPEG caution about alpha -> flatten onto white background).
6. Save overwrite path.
7. Invoke callback to refresh any UI thumbnail (controller can reload image & update CTkImage).

### Integration Points
- In `ui.py`, replace `command=lambda: self.on_thumbnail_click(self.meta.path)` handler to open editor instead of plain viewer. Provide controller method `open_image_editor(path)` that instantiates `ImageAnnotationEditor`.
- Keep `ImageViewerDialog` for context menu "View Only" (optional future).

### File / Module Structure Changes
- New file: `explora_doc/image_editor.py` with classes & logic above.
- Potential small addition in `ui.py`: new method on controller or UI to open editor.
- (Optional) Add `explora_doc/annotations.py` to hold dataclasses & tool enum if we want extra separation. Start with all in `image_editor.py` for simplicity; refactor later.

### Public API Surface
`ImageAnnotationEditor.open(parent, image_path, on_save)` -> classmethod convenience returning instance (handles modal setup & mainloop wait window).

### Pseudocode Skeleton
```python
class ImageAnnotationEditor:
    def __init__(self, parent, image_path: Path, on_save: Callable[[Path], None]):
        self.parent = parent
        self.path = image_path
        self.on_save = on_save
        self.annotations = []
        self.undo_stack = []
        self.redo_stack = []
        self.tool = ToolType.RECT
        self._load_image()
        self._build_ui()
        self._bind_events()

    def _push_state(self):
        self.undo_stack.append(copy.deepcopy(self.annotations))
        self.redo_stack.clear()

    def _undo(self): ...
    def _redo(self): ...
    def _on_mouse_down(self, event): ...
    def _on_mouse_move(self, event): ...
    def _on_mouse_up(self, event): ...
    def _render_canvas(self): ...
    def _composite_and_save(self): ...
    def _cancel(self): self.window.destroy()
```

### Edge Cases & Handling
- Large images exceeding screen: scale for display but keep original coordinates; maintain scale factor for mapping mouse coords back to image space.
- Unsupported format (e.g., cannot save with alpha): detect extension; if JPEG flatten overlay onto RGB.
- External modification while editing: store original mtime; before save compare; if mismatch prompt (basic messagebox) -> user can proceed.
- Undo when no history -> disable button as well as redo button.

### Minimal Dependencies
- Pillow (already present).
- customtkinter (already present).
- No new packages needed.

### Testing / Manual Verification Checklist
1. Open editor, draw rectangle & ellipse; Done -> image file updated (timestamp changes) & shapes visible in thumb.
2. Draw shape then Cancel -> original unchanged (compare hash or visual).
3. Add three annotations -> Undo thrice -> stack empties; Redo thrice restores.
4. Text commit with Enter; ESC cancels.
5. Highlight line snaps to horizontal, vertical, and diagonal at near angles.
6. JPEG vs PNG saving results correct (no alpha error for JPEG).
7. Modal behavior: main window unresponsive until editor closed.

### Rough Timeline / Steps
1. Implement data classes & enums.
2. Build editor UI skeleton with canvas & toolbar.
3. Implement tool switching & drawing interactions.
4. Add undo/redo state snapshot logic.
5. Implement highlight snapping.
6. Implement text entry overlay.
7. Composite + save logic with Pillow overlay.
8. Integrate with `ui.py` controller (new method) & replace thumbnail click.
9. Smoke test manually.
10. Refine visuals & disable buttons appropriately.

---
## Open Questions / Assumptions
- Assume images are PNGs (alpha ok); will still handle JPEG by flattening.
- Assume no need for selection/edit after creation in first version.
- Assume no concurrency issues (single-threaded Tk event loop).
- Assume main controller will supply a refresh mechanism after save.

END OF PLAN
