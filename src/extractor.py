"""
Text extraction module for PDF and image files.
Uses pdfplumber for PDFs and EasyOCR for images.
"""

import os
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> Tuple[str, list]:
    """
    Extract text from PDF using pdfplumber.
    Returns (extracted_text, pages_list).
    """
    import pdfplumber

    text_parts = []
    pages_info = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_parts.append(f"--- Page {page_num} ---\n{page_text.strip()}")
                pages_info.append({"page": page_num, "chars": len(page_text)})
            else:
                # Page might be image-based, try to extract from image
                logger.info(f"Page {page_num} has no selectable text, trying image extraction.")
                page_image = page.to_image(resolution=300)
                img_path = file_path + f"_page_{page_num}.png"
                page_image.save(img_path)
                try:
                    img_text = extract_text_from_image(img_path)
                    if img_text.strip():
                        text_parts.append(f"--- Page {page_num} (OCR) ---\n{img_text.strip()}")
                        pages_info.append({"page": page_num, "chars": len(img_text), "ocr": True})
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)

    return "\n\n".join(text_parts), pages_info


def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from image using EasyOCR.
    Falls back to pytesseract if available.
    """
    try:
        import easyocr
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        results = reader.readtext(file_path)
        lines = [text for (_, text, confidence) in results if confidence > 0.3]
        return "\n".join(lines)
    except ImportError:
        logger.warning("EasyOCR not available, trying pytesseract...")
        return _extract_with_pytesseract(file_path)
    except Exception as e:
        logger.error(f"EasyOCR failed: {e}, trying pytesseract...")
        return _extract_with_pytesseract(file_path)


def _extract_with_pytesseract(file_path: str) -> str:
    """Fallback OCR using pytesseract."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        return pytesseract.image_to_string(img, config="--psm 6")
    except ImportError:
        raise RuntimeError("Neither EasyOCR nor pytesseract is installed. Please install one of them.")


def extract_text(file_path: str) -> Tuple[str, str, list]:
    """
    Auto-detect file type and extract text.
    Returns (text, method_used, metadata).
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        text, meta = extract_text_from_pdf(file_path)
        return text, "pdfplumber", meta
    elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}:
        text = extract_text_from_image(file_path)
        return text, "easyocr", [{"file": Path(file_path).name}]
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP")
