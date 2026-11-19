import sys
import unittest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from modules.report_generation import (
    generate_csv_report,
    generate_pdf_report,
    generate_txt_report,
)


class ReportGenerationTests(unittest.TestCase):
    def setUp(self):
        self.fields = {
            "Person Name": "Rahul Sharma",
            "Organization": "Sunrise Technologies",
            "Email": "billing@example.com",
            "Phone": "+91 98765 43210",
            "Date": "19/11/2026",
            "Invoice Number": "INV-001",
            "Amount/Total": "1250.50",
            "Address": "123 Main Street",
            "Keywords": ["invoice", "total"],
        }
        self.analysis = {
            "document_type": "Invoice",
            "summary": "Detected document type: Invoice.",
            "detected_issues": [],
        }
        self.verification = {
            "overall_status": "Valid",
            "valid_count": 7,
            "warning_count": 0,
            "error_count": 0,
            "checks": [{"status": "Valid", "check": "Email format", "detail": "billing@example.com"}],
        }

    def test_txt_report(self):
        report = generate_txt_report("invoice.pdf", "INVOICE INV-001")
        self.assertIn(b"invoice.pdf", report)
        self.assertIn(b"INVOICE INV-001", report)

    def test_csv_report(self):
        report = generate_csv_report(self.fields)
        self.assertIn(b"Person Name", report)
        self.assertIn(b"Rahul Sharma", report)

    def test_pdf_report(self):
        report = generate_pdf_report(
            "invoice.pdf",
            self.fields,
            self.analysis,
            self.verification,
        )
        self.assertTrue(report.startswith(b"%PDF"))
        self.assertGreater(len(report), 500)


if __name__ == "__main__":
    unittest.main()
