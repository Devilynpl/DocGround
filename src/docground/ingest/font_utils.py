"""Font utility for ReportLab PDF generation with full Polish UTF-8 support."""

import os
import sys
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONTS_INITIALIZED = False

def register_polish_fonts() -> str:
    """Registers TrueType fonts that support Polish diacritics (ą, ć, ę, ł, ń, ó, ś, ź, ż).
    Returns the font family name to use ('Arial' or fallback).
    """
    global _FONTS_INITIALIZED
    if _FONTS_INITIALIZED:
        return "Arial"

    windows_font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    arial_regular = windows_font_dir / "arial.ttf"
    arial_bold = windows_font_dir / "arialbd.ttf"
    arial_italic = windows_font_dir / "ariali.ttf"
    arial_bold_italic = windows_font_dir / "arialbi.ttf"

    if arial_regular.exists():
        try:
            pdfmetrics.registerFont(TTFont("Arial", str(arial_regular)))
            if arial_bold.exists():
                pdfmetrics.registerFont(TTFont("Arial-Bold", str(arial_bold)))
            else:
                pdfmetrics.registerFont(TTFont("Arial-Bold", str(arial_regular)))

            if arial_italic.exists():
                pdfmetrics.registerFont(TTFont("Arial-Italic", str(arial_italic)))
            else:
                pdfmetrics.registerFont(TTFont("Arial-Italic", str(arial_regular)))

            if arial_bold_italic.exists():
                pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(arial_bold_italic)))
            else:
                pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(arial_regular)))

            pdfmetrics.registerFontFamily(
                "Arial",
                normal="Arial",
                bold="Arial-Bold",
                italic="Arial-Italic",
                boldItalic="Arial-BoldItalic",
            )
            try:
                import reportlab.platypus.tables as tables
                tables.CellStyle.fontname = "Arial"
                tables._baseFontName = "Arial"
            except Exception:
                pass
            _FONTS_INITIALIZED = True
            return "Arial"
        except Exception as e:
            print(f"[font_utils] Warning: Failed to register Arial: {e}")

    # Fallback to Helvetica
    return "Helvetica"
