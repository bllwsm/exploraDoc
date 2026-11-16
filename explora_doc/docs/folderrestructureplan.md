
### Proposed Modular Folder Structure (Lightweight & Clean)
Goal: Improve discoverability and separation of concerns without over-engineering. Keep flat where simple; group by responsibility when growth is likely.

```
explora_doc/
   __init__.py
   __main__.py                # Entry point (python -m explora_doc)
   app.py                     # App bootstrap / dependency wiring
   core/                      # Core domain & shared logic (no UI)
      __init__.py
      models.py                # Domain data classes (ScreenshotMeta, etc.)
      data_manager.py          # Persistence/session data handling
      file_monitor.py          # Folder monitoring / screenshot discovery
      exporter.py              # Export logic (Word / other formats)
      services/                # (Optional) Future service classes (e.g., OCR, redaction)
         __init__.py
   ui/                        # All UI components & widgets
      __init__.py
      main_ui.py               # MainUI class (moved from current ui.py)
      dialogs.py               # ImageViewerDialog, ExportSuccessDialog, confirm modals
      widgets/                 # Reusable composite widgets (future, e.g., toolbar, color picker)
         __init__.py
   editor/                    # Image annotation editor module(s)
      __init__.py
      annotations.py           # Annotation dataclasses & ToolType enum
      renderer.py              # Canvas & Pillow rendering helpers
      undo.py                  # Undo/redo manager (snapshot or command pattern)
      image_editor.py          # ImageAnnotationEditor (modal orchestration)
   assets/                    # Static assets (already exists)
      __init__.py
      icons/                   # Icons
      images/                  # Sample/background images
      fonts/ (optional)        # Custom fonts for text tool
   util/ (optional)           # Small generic helpers (logging wrappers, path utils)
      __init__.py
      paths.py
   config.py (optional)       # Centralized constants / settings
   feature.md (legacy?)       # Consider moving to docs/

tests/                       # (Optional) lightweight tests (pytest or unittest)
   test_annotations.py
   test_highlight_snap.py

docs/                        # Documentation & plan files
   ImageEditorPlan.md
   JIRA_INTEGRATION_SETUP.md  # (move from root if desired)
```

#### Rationale / What Goes Where
| Area | Put Here | Why |
|------|----------|-----|
core/* | Non-UI logic (monitoring, export, data persistence) | Keeps domain separate from presentation layer |
ui/* | Tk/CustomTkinter windows, frames, dialogs | Clear boundary so UI refactor doesn't touch logic |
editor/* | All annotation-specific code | Encapsulates a feature vertical (tools, rendering, undo) |
assets/* | Static resources only | Prevents code/assets mixing |
util/* | Truly generic helpers (avoid if only 1–2 functions) | Optional; prevents helper sprawl in random files |
docs/* | Markdown design & setup docs | Easier discovery than mixing with code |

#### Migration Steps (Incremental)
1. Create new folders: `ui`, `editor`, `core`, `docs`.
2. Move `models.py`, `data_manager.py`, `file_monitor.py`, `exporter.py` into `core/` (update imports: `from .core.models import ...`).
3. Split current `ui.py`:
    - `MainUI` & `ScreenshotEntryUI` -> `ui/main_ui.py`.
    - Dialog classes -> `ui/dialogs.py`.
    - Keep a thin legacy `ui.py` temporarily importing & re-exporting to avoid breaking external imports; later delete.
4. Add `editor/annotations.py`, `editor/renderer.py`, `editor/undo.py`, `editor/image_editor.py` during implementation (initial MVP could combine into one file; split later once stable).
5. Adjust controller references to new module paths.
6. Update `__all__` exports in `explora_doc/__init__.py` if you want a curated public API.
7. Run app & smoke test after each move to catch import errors early.

#### Minimal Import Changes Example
Before:
```python
from .models import ScreenshotMeta
from .ui import MainUI
```
After:
```python
from .core.models import ScreenshotMeta
from .ui.main_ui import MainUI
```

### Lightweight Dependency Flow
`ui.main_ui` -> (calls) `core.file_monitor`, `core.data_manager`, `editor.image_editor`.
`editor.image_editor` -> uses `editor.annotations`, `editor.undo`, Pillow.
`core.exporter` -> uses Pillow but NOT UI.

Arrow of dependency is inward towards core; nothing in `core/` should import from `ui/` or `editor/`.

