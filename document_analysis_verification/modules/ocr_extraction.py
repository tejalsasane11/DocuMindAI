"""Text extraction using PyMuPDF for digital PDFs and Tesseract OCR."""

import shutil
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
import pymupdf
import pytesseract


DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def configure_tesseract() -> Optional[str]:
    """Configure Tesseract if it is not available in the Windows PATH."""
    executable = shutil.which("tesseract")
    if executable:
        pytesseract.pytesseract.tesseract_cmd = executable
        return executable

    if Path(DEFAULT_TESSERACT_PATH).is_file():
        pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_PATH
        return DEFAULT_TESSERACT_PATH

    return None


def extract_text_from_image(
    image: np.ndarray,
    language: str = "eng",
    config: str = "--oem 3 --psm 6",
) -> Dict[str, str]:
    """Extract text from an image using Tesseract OCR."""
    if image is None or getattr(image, "size", 0) == 0:
        return {"text": "", "status": "error", "message": "The image is empty."}

    executable = configure_tesseract()
    if executable is None:
        return {
            "text": "",
            "status": "error",
            "message": "Tesseract OCR was not found. Install Tesseract and reopen the application.",
        }

    try:
        if len(image.shape) == 2:
            ocr_image = image
        elif image.shape[2] == 4:
            ocr_image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            ocr_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        text = pytesseract.image_to_string(
            ocr_image,
            lang=language,
            config=config,
        )
        text = text.strip()

        if not text:
            return {
                "text": "",
                "status": "warning",
                "message": "No readable text was detected in this image.",
            }

        return {"text": text, "status": "success", "message": "OCR completed successfully."}
    except pytesseract.TesseractNotFoundError:
        return {
            "text": "",
            "status": "error",
            "message": "Tesseract executable could not be started.",
        }
    except Exception as error:
        return {
            "text": "",
            "status": "error",
            "message": f"OCR failed: {error}",
        }


def extract_text_from_pdf(
    pdf_bytes: bytes,
    dpi: int = 150,
    minimum_text_characters: int = 40,
) -> Dict[str, object]:
    """Extract selectable PDF text and OCR sparse or scanned pages."""
    if not pdf_bytes:
        return {"text": "", "pages": [], "status": "error", "message": "The PDF is empty."}

    page_results: List[Dict[str, object]] = []
    all_text: List[str] = []

    try:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
            scale = dpi / 72
            matrix = pymupdf.Matrix(scale, scale)

            for page_number, page in enumerate(document, start=1):
                digital_text = page.get_text("text").strip()
                extraction_method = "digital text"

                if len(digital_text) < minimum_text_characters:
                    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                    image_bytes = pixmap.tobytes("png")
                    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                    rendered_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                    if rendered_image is not None:
                        ocr_result = extract_text_from_image(rendered_image)
                        ocr_text = str(ocr_result["text"])
                        if len(ocr_text.strip()) > len(digital_text.strip()):
                            digital_text = ocr_text
                            extraction_method = "OCR"

                clean_text = digital_text.strip()
                all_text.append(clean_text)
                page_results.append(
                    {
                        "page_number": page_number,
                        "text": clean_text,
                        "method": extraction_method,
                        "character_count": len(clean_text),
                    }
                )
    except Exception as error:
        return {
            "text": "",
            "pages": [],
            "status": "error",
            "message": f"Could not read the PDF: {error}",
        }

    combined_text = "\n\n".join(
        f"--- Page {page['page_number']} ---\n{page['text']}"
        for page in page_results
        if str(page["text"]).strip()
    ).strip()

    if not combined_text:
        return {
            "text": "",
            "pages": page_results,
            "status": "warning",
            "message": "No readable text was found in the PDF.",
        }

    return {
        "text": combined_text,
        "pages": page_results,
        "status": "success",
        "message": "PDF text extraction completed.",
    }
