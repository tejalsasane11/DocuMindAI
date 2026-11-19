import sys
import unittest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from modules.document_analysis import (
    analyze_document,
    detect_document_type,
    find_duplicate_values,
    find_missing_fields,
)


class DocumentAnalysisTests(unittest.TestCase):
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
            "All Emails": ["billing@example.com", "billing@example.com"],
            "All Phones": ["+91 98765 43210"],
            "All Dates": ["19/11/2026"],
        }

    def test_detect_invoice(self):
        text = "INVOICE Invoice Number: INV-001 Total Amount: 1250.50 Bill To: Rahul"
        self.assertEqual(detect_document_type(text), "Invoice")

    def test_detect_other_document(self):
        self.assertEqual(detect_document_type("General notes for a project meeting"), "Other Document")

    def test_missing_fields(self):
        incomplete = dict(self.fields)
        incomplete["Phone"] = "Not Found"
        missing = find_missing_fields(incomplete, "Invoice")
        self.assertIn("Phone", missing)

    def test_duplicate_values(self):
        duplicates = find_duplicate_values(self.fields)
        self.assertTrue(any("Email" in item for item in duplicates))

    def test_full_analysis(self):
        text = "INVOICE Invoice Number: INV-001 Total Amount: 1250.50"
        result = analyze_document(text, self.fields)
        self.assertEqual(result["document_type"], "Invoice")
        self.assertIn("Duplicate Email", result["duplicate_information"][0])
        self.assertIn("summary", result)

    def test_negative_amount(self):
        fields = dict(self.fields)
        fields["Amount/Total"] = "-50"
        result = analyze_document("INVOICE total -50", fields)
        self.assertIn("Amount/Total is negative.", result["unusual_values"])


if __name__ == "__main__":
    unittest.main()
