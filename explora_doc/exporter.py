"""Document export functionality."""

from pathlib import Path
from typing import Dict
from docx import Document
from docx.shared import Inches
import os

from .models import ScreenshotMeta


class DocumentExporter:
    """Handles exporting screenshots and annotations to Word documents."""
    
    @staticmethod
    def export_to_word(screenshots: Dict[Path, ScreenshotMeta], test_title: str = "Exploratory Test Session") -> Path:
        """
        Export screenshots and annotations to a Word document.
        
        Args:
            screenshots: Dictionary mapping file paths to screenshot metadata
            test_title: Title for the test session
            
        Returns:
            Path: Full path to the created document
            
        Raises:
            Exception: If document creation fails
        """
        if not screenshots:
            raise ValueError("No screenshots to export")
        
        doc = Document()
        doc.add_heading(test_title, level=1)
        # Set default font for the document to Arial
        from docx.oxml.ns import qn
        from docx.shared import Pt
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Arial'
        font.size = Pt(11)
        # For compatibility with Word
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
        
        # Process screenshots in the order they appear in the dictionary
        figure_number = 1
        for path, meta in screenshots.items():
            # Add image
            try:
                doc.add_picture(str(path), width=Inches(6.0))
                
                # Add caption as a proper figure caption if provided
                caption = meta.caption.get().strip()
                if caption:
                    caption_paragraph = doc.add_paragraph()
                    run = caption_paragraph.add_run(f"Figure {figure_number}: {caption}")
                    caption_paragraph.style = 'Caption'  # Use Word's built-in caption style
                    caption_paragraph.alignment = 1  # Center alignment
                    run.font.name = 'Arial'
                else:
                    # If no caption, still add a numbered figure label
                    caption_paragraph = doc.add_paragraph()
                    run = caption_paragraph.add_run(f"Figure {figure_number}")
                    caption_paragraph.style = 'Caption'
                    caption_paragraph.alignment = 1
                    run.font.name = 'Arial'
                figure_number += 1
            except Exception as e:
                error_paragraph = doc.add_paragraph(f"[Image error: {e}]")
                for run in error_paragraph.runs:
                    run.font.name = 'Arial'
            
            # Add what this image shows
            what_content = meta.what.get().strip()
            if what_content:
                what_paragraph = doc.add_paragraph(what_content)
                for run in what_paragraph.runs:
                    run.font.name = 'Arial'
            
            # Add branch label
            branch = meta.branch.get()
            if branch:
                branch_paragraph = doc.add_paragraph(f"Branch: {branch}")
                for run in branch_paragraph.runs:
                    run.font.name = 'Arial'
            
            doc.add_page_break()
        
        # Generate filename based on test title
        # Clean the title to make it filesystem-safe
        safe_title = "".join(c for c in test_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        if not safe_title:
            safe_title = "ExploraDoc"
        filename = f"{safe_title}.docx"
        
        # Save to user's Downloads folder
        downloads_path = Path.home() / "Downloads"
        downloads_path.mkdir(exist_ok=True)  # Ensure Downloads folder exists
        file_path = downloads_path / filename
        
        doc.save(str(file_path))
        return file_path
