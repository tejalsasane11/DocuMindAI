"""Image preprocessing helpers for improving OCR accuracy."""

from typing import Any, Dict, Tuple

import cv2
import numpy as np


DEFAULT_MAX_WIDTH = 2400
DEFAULT_MAX_HEIGHT = 2400


def validate_image(image: np.ndarray) -> None:
    """Raise a clear error when an image is not usable."""
    if image is None:
        raise ValueError("The image is empty or could not be loaded.")
    if not isinstance(image, np.ndarray):
        raise TypeError("The image must be a NumPy array.")
    if image.size == 0:
        raise ValueError("The image contains no pixels.")


def to_bgr(image: np.ndarray) -> np.ndarray:
    """Convert an image to a three-channel BGR NumPy array."""
    validate_image(image)

    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.ndim == 3 and image.shape[2] == 1:
        return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    if image.ndim == 3 and image.shape[2] == 3:
        return image.copy()

    raise ValueError("Unsupported image format.")


def resize_image(
    image: np.ndarray,
    max_width: int = DEFAULT_MAX_WIDTH,
    max_height: int = DEFAULT_MAX_HEIGHT,
) -> np.ndarray:
    """Downscale an image if it exceeds the configured maximum dimensions."""
    validate_image(image)
    bgr = to_bgr(image)
    height, width = bgr.shape[:2]

    if width <= max_width and height <= max_height:
        return bgr

    scale = min(max_width / width, max_height / height)
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    return cv2.resize(bgr, (new_width, new_height), interpolation=cv2.INTER_AREA)


def grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR or BGRA image to grayscale."""
    bgr = to_bgr(image)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def remove_noise(image: np.ndarray, strength: int = 5) -> np.ndarray:
    """Remove small noise while preserving document text and edges."""
    gray = grayscale(image)
    strength = max(1, min(31, strength))
    if strength % 2 == 0:
        strength += 1
    return cv2.GaussianBlur(gray, (strength, strength), 0)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Improve contrast using histogram equalization."""
    gray = grayscale(image)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def apply_threshold(image: np.ndarray) -> np.ndarray:
    """Convert a grayscale image to a binary image for OCR."""
    gray = grayscale(image)
    enhanced = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        10,
    )


def preprocess_image(
    image: np.ndarray,
    resize: bool = True,
    denoise: bool = True,
    enhance: bool = True,
    threshold: bool = True,
) -> Dict[str, np.ndarray]:
    """Run the preprocessing pipeline and retain each useful intermediate image."""
    validate_image(image)

    original = to_bgr(image)
    processed = resize_image(original) if resize else original
    gray = grayscale(processed)

    denoised = remove_noise(processed) if denoise else gray
    contrasted = enhance_contrast(denoised) if enhance else denoised
    binary = apply_threshold(contrasted) if threshold else contrasted

    return {
        "original": original,
        "resized": processed,
        "grayscale": gray,
        "denoised": denoised,
        "contrasted": contrasted,
        "binary": binary,
        "ocr_ready": binary,
    }


def preprocess_document(image: np.ndarray) -> Dict[str, np.ndarray]:
    """Convenience function for the default OCR preprocessing pipeline."""
    return preprocess_image(image)
