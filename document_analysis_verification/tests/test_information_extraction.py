import sys
import unittest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from modules.information_extraction import (
    NOT_FOUND,
    extract_structured_information,
)


class InformationExtractionTests(unittest.TestCase):
    def setUp(self):
        self.text = """
INVOICE
Invoice Number: INV-2026-0042
Date: 19/11/2026
Customer Name: Rahul Sharma
Organization: Sunrise Technologies
Email: billing@sunrise.example
Phone: +91 98765 43210
Address: 123 Main Street, Pune
Total Amount: $1,250.50
"""

    def test_extract_expected_fields(self):
        fields = extract_structured_information(self.text)
        self.assertEqual(fields["Invoice Number"], "INV-2026-0042")
        self.assertEqual(fields["Person Name"], "Rahul Sharma")
        self.assertEqual(fields["Organization"], "Sunrise Technologies")
        self.assertEqual(fields["Email"], "billing@sunrise.example")
        self.assertIn("98765", fields["Phone"])
        self.assertEqual(fields["Date"], "19/11/2026")

    def test_extract_amount(self):
        fields = extract_structured_information(self.text)
        self.assertEqual(fields["Amount/Total"], "1,250.50")

    def test_extract_address(self):
        fields = extract_structured_information(self.text)
        self.assertEqual(fields["Address"], "123 Main Street, Pune")

    def test_missing_fields_are_not_invented(self):
        fields = extract_structured_information("This is a simple document with no labels.")
        self.assertEqual(fields["Email"], NOT_FOUND)
        self.assertEqual(fields["Phone"], NOT_FOUND)
        self.assertEqual(fields["Invoice Number"], NOT_FOUND)
        self.assertEqual(fields["Amount/Total"], NOT_FOUND)

    def test_empty_text(self):
        fields = extract_structured_information("")
        self.assertEqual(fields["Organization"], NOT_FOUND)
        self.assertEqual(fields["Keywords"], [])

    def test_application_specific_fields(self):
        text = "APPLICATION FORM\nApplication Number: APP-001\nApplicant Name: Tejal Patil\nEmail: tejal@example.com\nPhone: 9876543210\nAddress: 12 College Road\nApplication Date: 11/11/2026"
        fields = extract_structured_information(text)
        self.assertEqual(fields["Applicant Name"], "Tejal Patil")
        self.assertEqual(fields["Application Number"], "APP-001")

    def test_receipt_specific_fields(self):
        text = "PAYMENT RECEIPT\nReceipt Number: RCT-1\nShop Name: Fresh Store\nTransaction Date: 10/11/2026\nPaid Amount: 850.00\nPayment Method: UPI"
        fields = extract_structured_information(text)
        self.assertEqual(fields["Receipt Number"], "RCT-1")
        self.assertEqual(fields["Shop Name"], "Fresh Store")
        self.assertEqual(fields["Payment Method"], "UPI")

    def test_certificate_specific_fields(self):
        text = "CERTIFICATE\nCertificate Number: CERT-1\nStudent Name: Priya Nair\nInstitution: National Institute\nIssue Date: 15/11/2026\nCourse: AI"
        fields = extract_structured_information(text)
        self.assertEqual(fields["Certificate ID"], "CERT-1")
        self.assertEqual(fields["Person Name"], "Priya Nair")


if __name__ == "__main__":
    unittest.main()
