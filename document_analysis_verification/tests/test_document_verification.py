import sys
import unittest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from modules.document_verification import (
    valid_amount,
    valid_date,
    valid_email,
    valid_phone,
    verify_document,
)


class DocumentVerificationTests(unittest.TestCase):
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
        }
        self.analysis = {"document_type": "Invoice", "duplicate_information": [], "unusual_values": []}

    def test_valid_email(self):
        self.assertTrue(valid_email("student@example.com"))
        self.assertFalse(valid_email("student@invalid"))

    def test_valid_phone(self):
        self.assertTrue(valid_phone("+91 98765 43210"))
        self.assertFalse(valid_phone("123"))

    def test_valid_date(self):
        self.assertTrue(valid_date("19/11/2026"))
        self.assertFalse(valid_date("31/13/2026"))

    def test_valid_amount(self):
        self.assertTrue(valid_amount("1,250.50"))
        self.assertFalse(valid_amount("unknown"))

    def test_overall_valid_status(self):
        result = verify_document(self.fields, self.analysis)
        self.assertEqual(result["overall_status"], "Valid")

    def test_warning_status_for_missing_field(self):
        fields = dict(self.fields)
        fields["Phone"] = "Not Found"
        result = verify_document(fields, self.analysis)
        self.assertEqual(result["overall_status"], "Warning")

    def test_error_status_for_invalid_email(self):
        fields = dict(self.fields)
        fields["Email"] = "invalid-email"
        result = verify_document(fields, self.analysis)
        self.assertEqual(result["overall_status"], "Error")


if __name__ == "__main__":
    unittest.main()
