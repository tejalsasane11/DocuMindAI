"""Document upload validation and preview helpers."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import io

import numpy as np
from PIL import Image
import pymupdf

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_uploaded_file(file: Any) -> Tuple[bool, str]:
    """Validate an uploaded Streamlit file or a file-like object."""
    try:
        file_name = getattr(file, "name", "")
        extension = Path(file_name).suffix.lower()

        if not file_name:
            return False, "The uploaded file has no filename."
        if extension not in ALLOWED_EXTENSIONS:
            return False, "Unsupported file type. Please upload PDF, JPG, JPEG, or PNG."

        file_bytes = file.getvalue() if hasattr(file, "getvalue") else file.read()
        if not file_bytes:
            return False, "The uploaded file is empty."
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            return False, f"File exceeds the {MAX_FILE_SIZE_MB} MB upload limit."

        if extension == ".pdf":
            try:
                with pymupdf.open(stream=file_bytes, filetype="pdf") as document:
                    if document.page_count == 0:
                        return False, "The PDF does not contain any pages."
            except Exception:
                return False, "The PDF is invalid or could not be opened."
        else:
            try:
                with Image.open(io.BytesIO(file_bytes)) as image:
                    image.verify()
            except Exception:
                return False, "The image file is invalid or unreadable."

        return True, "File validation passed."
    except Exception as error:
        return False, f"Could not validate the uploaded file: {error}"


def get_file_bytes(file: Any) -> bytes:
    """Get bytes from a Streamlit upload or file-like object."""
    if hasattr(file, "getvalue"):
        result = file.getvalue()
    elif hasattr(file, "read"):
        result = file.read()
    else:
        raise TypeError("The uploaded file must provide getvalue() or read().")

    if not isinstance(result, bytes):
        raise TypeError("The uploaded file content is not in bytes format.")
    return result


def get_file_info(file: Any) -> Dict[str, Any]:
    """Return basic information about an uploaded document."""
    file_name = getattr(file, "name", "unknown-document")
    file_bytes = get_file_bytes(file)
    extension = Path(file_name).suffix.lower().replace(".", "")

    return {
        "file_name": file_name,
        "file_type": extension.upper(),
        "file_size_bytes": len(file_bytes),
        "file_size_mb": round(len(file_bytes) / (1024 * 1024), 2),
    }


def bytes_to_image(file_bytes: bytes) -> Optional[np.ndarray]:
    """Convert JPG or PNG bytes to an OpenCV-compatible RGB image."""
    try:
        with Image.open(io.BytesIO(file_bytes)) as image:
            rgb_image = np.array(image.convert("RGB"))
            return rgb_image[:, :, ::-1]
    except Exception:
        return None


def pdf_bytes_to_page_images(
    file_bytes: bytes,
    dpi: int = 150,
) -> List[Tuple[int, np.ndarray, bytes]]:
    """Render PDF pages as OpenCV-compatible and PNG-preview images."""
    rendered_pages: List[Tuple[int, np.ndarray, bytes]] = []

    try:
        with pymupdf.open(stream=file_bytes, filetype="pdf") as document:
            scale = dpi / 72
            matrix = pymupdf.Matrix(scale, scale)

            for page_number, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                png_bytes = pixmap.tobytes("png")

                pil_image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
                rgb_array = np.array(pil_image)
                bgr_array = rgb_array[:, :, ::-1]
                rendered_pages.append((page_number, bgr_array, png_bytes))
    except Exception:
        return []

    return rendered_pages


def load_document_preview(file: Any) -> Dict[str, Any]:
    """Load a validated image or PDF and return its preview pages."""
    file_bytes = get_file_bytes(file)
    file_name = getattr(file, "name", "unknown-document")
    extension = Path(file_name).suffix.lower()

    if extension == ".pdf":
        pages = pdf_bytes_to_page_images(file_bytes)
        return {
            "document_type": "PDF",
            "file_bytes": file_bytes,
            "pages": pages,
        }

    image = bytes_to_image(file_bytes)
    if image is None:
        return {"document_type": "IMAGE", "file_bytes": file_bytes, "pages": []}

    return {
        "document_type": "IMAGE",
        "file_bytes": file_bytes,
        "pages": [(1, image, file_bytes)],
    }
