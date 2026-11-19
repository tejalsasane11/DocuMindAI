import sys
import unittest

import cv2
import numpy as np
import pymupdf

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from modules.ocr_extraction import (
    configure_tesseract,
    extract_text_from_image,
    extract_text_from_pdf,
)


class OCRExtractionTests(unittest.TestCase):
    def test_tesseract_is_available(self):
        self.assertIsNotNone(configure_tesseract())

    def test_extract_text_from_clear_image(self):
        image = np.full((200, 600, 3), 255, dtype=np.uint8)
        cv2.putText(
            image,
            "INVOICE TEST",
            (50, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 0),
            3,
            cv2.LINE_AA,
        )

        result = extract_text_from_image(image)
        self.assertIn(result["status"], {"success", "warning"})
        if result["status"] == "success":
            self.assertIn("INVOICE", result["text"].upper())

    def test_extract_text_from_empty_image(self):
        result = extract_text_from_image(np.array([]))
        self.assertEqual(result["status"], "error")

    def test_extract_digital_pdf_text(self):
        pdf = pymupdf.open()
        page = pdf.new_page(width=595, height=842)
        page.insert_text(
            (72, 100),
            "INVOICE NUMBER INV-2026-001\nTOTAL AMOUNT $1250.50\nEMAIL billing@example.com",
            fontsize=12,
        )
        pdf_bytes = pdf.tobytes()
        pdf.close()

        result = extract_text_from_pdf(pdf_bytes)
        self.assertEqual(result["status"], "success")
        self.assertIn("INV-2026-001", result["text"])
        self.assertEqual(result["pages"][0]["method"], "digital text")

    def test_empty_pdf_bytes(self):
        result = extract_text_from_pdf(b"")
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
