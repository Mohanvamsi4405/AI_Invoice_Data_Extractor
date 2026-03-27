"""
Text extraction module for PDF and image files.
- PDF: pdfplumber (pure Python, excellent accuracy)
- Image: pytesseract (Tesseract OCR wrapper)
"""

import os
import logging
from pathlib import Path
from typing import Tuple, List

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> Tuple[str, List[dict]]:
    """Extract text from PDF using pdfplumber."""
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
                # Scanned page — try OCR via image
                logger.info(f"Page {page_num}: no selectable text, attempting OCR...")
                try:
                    img_path = file_path + f"_p{page_num}.png"
                    page_image = page.to_image(resolution=300)
                    page_image.save(img_path)
                    ocr_text = _ocr_image(img_path)
                    if ocr_text.strip():
                        text_parts.append(f"--- Page {page_num} (OCR) ---\n{ocr_text.strip()}")
                        pages_info.append({"page": page_num, "chars": len(ocr_text), "ocr": True})
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)

    return "\n\n".join(text_parts), pages_info


def _ocr_image(file_path: str) -> str:
    """OCR an image file using pytesseract."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        # PSM 6 = assume a uniform block of text
        return pytesseract.image_to_string(img, config="--psm 6")
    except Exception as e:
        logger.error(f"OCR failed for {file_path}: {e}")
        return ""


def extract_text(file_path: str) -> Tuple[str, str, List[dict]]:
    """
    Auto-detect file type and extract text.
    Returns (text, method_used, metadata).
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        text, meta = extract_text_from_pdf(file_path)
        return text, "pdfplumber", meta

    elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}:
        text = _ocr_image(file_path)
        return text, "pytesseract", [{"file": Path(file_path).name}]

    else:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            "Supported: PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP"
        )
