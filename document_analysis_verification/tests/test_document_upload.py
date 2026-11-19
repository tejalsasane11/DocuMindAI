import io
import sys
import unittest

import pymupdf
from PIL import Image

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from modules.document_upload import (
    get_file_info,
    load_document_preview,
    validate_uploaded_file,
)


class InMemoryUpload:
    def __init__(self, name, content):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content

    def read(self):
        return self._content


class DocumentUploadTests(unittest.TestCase):
    def test_valid_png(self):
        buffer = io.BytesIO()
        Image.new("RGB", (300, 200), color="white").save(buffer, format="PNG")
        upload = InMemoryUpload("sample.png", buffer.getvalue())

        valid, message = validate_uploaded_file(upload)
        self.assertTrue(valid, message)

        preview = load_document_preview(upload)
        self.assertEqual(preview["document_type"], "IMAGE")
        self.assertEqual(len(preview["pages"]), 1)

    def test_valid_pdf(self):
        pdf = pymupdf.open()
        page = pdf.new_page(width=595, height=842)
        page.insert_text((72, 72), "Test Invoice", fontsize=18)
        pdf_bytes = pdf.tobytes()
        pdf.close()

        upload = InMemoryUpload("invoice.pdf", pdf_bytes)
        valid, message = validate_uploaded_file(upload)
        self.assertTrue(valid, message)

        preview = load_document_preview(upload)
        self.assertEqual(preview["document_type"], "PDF")
        self.assertEqual(len(preview["pages"]), 1)

    def test_invalid_extension(self):
        upload = InMemoryUpload("document.txt", b"test content")
        valid, message = validate_uploaded_file(upload)
        self.assertFalse(valid)
        self.assertIn("Unsupported file type", message)

    def test_empty_file(self):
        upload = InMemoryUpload("empty.png", b"")
        valid, message = validate_uploaded_file(upload)
        self.assertFalse(valid)
        self.assertIn("empty", message.lower())

    def test_file_info(self):
        upload = InMemoryUpload("certificate.jpg", b"123456")
        info = get_file_info(upload)
        self.assertEqual(info["file_name"], "certificate.jpg")
        self.assertEqual(info["file_type"], "JPG")


if __name__ == "__main__":
    unittest.main()
