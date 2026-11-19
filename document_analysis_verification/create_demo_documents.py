"""Create five printable demo PDF documents for the Streamlit application."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


OUTPUT_DIR = Path(__file__).resolve().parent / "sample_documents"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_demo_pdf(file_name: str, title: str, fields: list, extra_lines: list = None):
    pdf_path = OUTPUT_DIR / file_name
    document = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                  rightMargin=18 * mm, leftMargin=18 * mm,
                                  topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 8 * mm),
        Table([["Document Field", "Information"]] + [[name, value] for name, value in fields],
              colWidths=[55 * mm, 105 * mm], repeatRows=1,
              style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1F4E78")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
                  ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#777777")),
                  ("VALIGN", (0, 0), (-1, -1), "TOP"),
                  ("LEFTPADDING", (0, 0), (-1, -1), 6),
                  ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                  ("TOPPADDING", (0, 0), (-1, -1), 5),
                  ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
              ])),
        Spacer(1, 8 * mm),
    ]

    for line in extra_lines or []:
        story.append(Paragraph(line, styles["Normal"]))

    document.build(story)
    print(pdf_path)


create_demo_pdf("01_complete_invoice.pdf", "INVOICE", [
    ("Invoice Number", "INV-2026-0042"),
    ("Date", "19/11/2026"),
    ("Customer Name", "Rahul Sharma"),
    ("Organization", "Sunrise Technologies"),
    ("Email", "billing@sunrise.example"),
    ("Phone", "+91 98765 43210"),
    ("Address", "123 Main Street, Pune"),
    ("Subtotal", "₹1,000.00"),
    ("Tax", "₹250.50"),
    ("Total Amount", "₹1,250.50"),
], ["Payment Status: Due", "Please retain this document for your records."])

create_demo_pdf("02_receipt.pdf", "PAYMENT RECEIPT", [
    ("Receipt Number", "RCT-2026-018"),
    ("Date", "18/11/2026"),
    ("Customer Name", "Aarav Patel"),
    ("Organization", "BlueBridge Store"),
    ("Email", "accounts@bluebridge.example"),
    ("Phone", "022 4567 8910"),
    ("Paid Amount", "₹850.00"),
    ("Payment Method", "UPI"),
], ["Payment Received", "Change Due: ₹0.00"])

create_demo_pdf("03_certificate.pdf", "CERTIFICATE OF COMPLETION", [
    ("Certificate Number", "CERT-2026-AI-110"),
    ("Student Name", "Priya Nair"),
    ("Institution", "National Institute of Technology"),
    ("Date", "15/11/2026"),
    ("Course", "Artificial Intelligence and Data Science"),
], ["This certificate confirms successful course completion.", "Awarded for outstanding academic performance."])

create_demo_pdf("04_application_form.pdf", "STUDENT APPLICATION FORM", [
    ("Application Number", "APP-2026-7781"),
    ("Applicant Name", "Neha Kulkarni"),
    ("Organization", "Tech University"),
    ("Email", "neha.kulkarni@example.com"),
    ("Phone", "+91 99887 76655"),
    ("Address", "45 Lake Road, Nashik"),
    ("Date", "12/11/2026"),
    ("Program", "Master of Artificial Intelligence"),
], ["Applicant Declaration: The information submitted is true to the applicant's knowledge."])

create_demo_pdf("05_project_report.pdf", "PROJECT COMPLETION REPORT", [
    ("Organization", "DocuMind Research Group"),
    ("Date", "10/11/2026"),
    ("Report Number", "RPT-2026-09"),
    ("Project Name", "Intelligent Document Verification System"),
], ["Summary: The project achieved document upload, OCR, field extraction, and rule-based verification.",
      "Findings: PDF text extraction performs better for digital documents; scanned pages require OCR.",
      "Conclusion: The implemented system provides explainable document analysis without legal-authenticity claims."])
