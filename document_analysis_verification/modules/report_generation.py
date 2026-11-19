"""TXT, CSV, and PDF report generation helpers."""

import io
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_txt_report(document_name: str, extracted_text: str) -> bytes:
    report = f"Extracted Text Report\nDocument: {document_name}\n{'=' * 60}\n\n{extracted_text or 'No text extracted.'}\n"
    return report.encode("utf-8")


def generate_csv_report(fields: Dict[str, object]) -> bytes:
    rows = []
    for name, value in fields.items():
        if isinstance(value, (list, tuple, set)):
            value = ", ".join(str(item) for item in value) if value else "Not Found"
        rows.append({"Field": name, "Extracted Value": str(value)})

    frame = pd.DataFrame(rows)
    return frame.to_csv(index=False).encode("utf-8-sig")


def generate_pdf_report(
    document_name: str,
    fields: Dict[str, object],
    analysis: Dict[str, object],
    verification: Dict[str, object],
) -> bytes:
    """Create a PDF report and return it as downloadable bytes."""
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Document Analysis Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1F4E78"),
        spaceAfter=12,
    )

    story = [
        Paragraph("Document Analysis and Verification Report", title_style),
        Paragraph(f"<b>Document:</b> {document_name}", styles["Normal"]),
        Spacer(1, 5 * mm),
    ]

    story.append(Paragraph("Analysis Summary", styles["Heading2"]))
    story.append(Paragraph(str(analysis.get("summary", "No analysis summary available.")), styles["Normal"]))

    summary_rows = [["Overall Status", str(verification.get("overall_status", "Warning"))],
                    ["Valid Checks", str(verification.get("valid_count", 0))],
                    ["Warnings", str(verification.get("warning_count", 0))],
                    ["Errors", str(verification.get("error_count", 0))]]
    summary_table = Table(summary_rows, colWidths=[45 * mm, 100 * mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F6FA")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([summary_table, Spacer(1, 5 * mm)])

    story.append(Paragraph("Extracted Information", styles["Heading2"]))
    field_rows = [["Field", "Extracted Value"]]
    for name, value in fields.items():
        if name.startswith("All ") or name == "Keywords":
            continue
        if isinstance(value, (list, tuple, set)):
            value = ", ".join(str(item) for item in value) if value else "Not Found"
        field_rows.append([str(name), str(value)])

    field_table = Table(field_rows, colWidths=[55 * mm, 90 * mm], repeatRows=1)
    field_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([field_table, Spacer(1, 5 * mm)])

    story.append(Paragraph("Verification Results", styles["Heading2"]))
    verification_rows = [["Status", "Check", "Detail"]]
    for check in verification.get("checks", []):
        verification_rows.append([
            str(check.get("status", "")),
            str(check.get("check", "")),
            str(check.get("detail", "")),
        ])

    verification_table = Table(verification_rows, colWidths=[20 * mm, 55 * mm, 70 * mm], repeatRows=1)
    verification_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.extend([verification_table, Spacer(1, 5 * mm)])

    detected_issues = analysis.get("detected_issues", [])
    story.append(Paragraph("Detected Issues", styles["Heading2"]))
    if detected_issues:
        for issue in detected_issues:
            story.append(Paragraph(f"• {issue}", styles["Normal"]))
    else:
        story.append(Paragraph("No automatic issues detected.", styles["Normal"]))

    story.extend([
        Spacer(1, 5 * mm),
        Paragraph("Disclaimer", styles["Heading2"]),
        Paragraph(
            "This application reports the results of implemented data-format and consistency checks only. "
            "It does not establish that a document is legally authentic or officially verified.",
            styles["Normal"],
        ),
    ])

    document.build(story)
    return buffer.getvalue()
