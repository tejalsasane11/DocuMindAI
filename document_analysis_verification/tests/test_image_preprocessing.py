import sys
import unittest

import cv2
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from modules.image_preprocessing import (
    apply_threshold,
    enhance_contrast,
    grayscale,
    preprocess_document,
    resize_image,
)


class ImagePreprocessingTests(unittest.TestCase):
    def setUp(self):
        self.image = np.full((300, 400, 3), 180, dtype=np.uint8)
        cv2.putText(
            self.image,
            "TEST DOCUMENT",
            (60, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (20, 20, 20),
            2,
        )

    def test_grayscale_has_one_channel(self):
        gray = grayscale(self.image)
        self.assertEqual(gray.ndim, 2)
        self.assertEqual(gray.shape, (300, 400))

    def test_resize_reduces_large_image(self):
        resized = resize_image(self.image, max_width=200, max_height=150)
        self.assertEqual(resized.shape[:2], (150, 200))

    def test_threshold_has_binary_values(self):
        binary = apply_threshold(self.image)
        unique_values = set(np.unique(binary).tolist())
        self.assertTrue(unique_values.issubset({0, 255}))

    def test_contrast_enhancement(self):
        contrasted = enhance_contrast(self.image)
        self.assertEqual(contrasted.shape, (300, 400))

    def test_preprocessing_pipeline(self):
        result = preprocess_document(self.image)

        self.assertIn("original", result)
        self.assertIn("ocr_ready", result)
        self.assertEqual(result["original"].shape, (300, 400, 3))
        self.assertEqual(result["ocr_ready"].ndim, 2)

    def test_empty_image_is_rejected(self):
        with self.assertRaises(ValueError):
            preprocess_document(np.array([]))


if __name__ == "__main__":
    unittest.main()
