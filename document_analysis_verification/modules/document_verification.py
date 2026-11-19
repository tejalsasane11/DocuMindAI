"""Explainable rule-based checks for extracted document information."""

import re
from datetime import datetime
from typing import Dict, List


NOT_FOUND = "Not Found"


def add_check(results: List[Dict[str, str]], status: str, name: str, detail: str) -> None:
    results.append({"status": status, "check": name, "detail": detail})


def is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().lower() == NOT_FOUND.lower()
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    return False


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value))


def valid_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 7 <= len(digits) <= 15


def valid_date(value: str) -> bool:
    formats = (
        "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d",
        "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y",
    )
    for date_format in formats:
        try:
            datetime.strptime(value.strip(), date_format)
            return True
        except ValueError:
            continue
    return False


def valid_amount(value: str) -> bool:
    try:
        normalized = re.sub(r"[$€£₹I, ]", "", value.strip())
        number = float(normalized)
        return number >= 0
    except (TypeError, ValueError):
        return False


def verify_document(fields: Dict[str, object], analysis: Dict[str, object]) -> Dict[str, object]:
    """Run document-type-specific rule checks and explain each result."""
    checks: List[Dict[str, str]] = []
    document_type = str(analysis.get("document_type", "General Document"))

    rules = {
        "Invoice": [
            ("Invoice Number", "Invoice number"),
            ("Invoice Date", "Invoice date"),
            ("Total Amount", "Total amount"),
        ],
        "Receipt": [
            ("Receipt Number", "Receipt number"),
            ("Date", "Transaction date"),
            ("Total Amount", "Receipt total"),
        ],
        "Certificate": [
            ("Person Name", "Certificate recipient"),
            ("Issue Date", "Certificate issue date"),
        ],
        "Application Form": [
            ("Applicant Name", "Applicant name"),
            ("Email", "Applicant email"),
            ("Phone", "Applicant phone"),
            ("Address", "Applicant address"),
        ],
        "Report": [
            ("Report Title", "Report title"),
            ("Organization", "Organization"),
            ("Date", "Report date"),
        ],
        "General Document": [],
    }

    for field_name, label in rules.get(document_type, []):
        value = fields.get(field_name)
        if is_missing(value):
            add_check(checks, "Warning", f"Missing {label}", f"The {label.lower()} was not found.")
        else:
            add_check(checks, "Valid", f"Present {label}", f"The {label.lower()} is present: {value}")

    email = fields.get("Email")
    if document_type in {"Invoice", "Application Form"} and not is_missing(email):
        if valid_email(str(email)):
            add_check(checks, "Valid", "Email format", str(email))
        else:
            add_check(checks, "Error", "Email format", f"Invalid email address: {email}")

    phone = fields.get("Phone")
    if document_type in {"Invoice", "Application Form"} and not is_missing(phone):
        if valid_phone(str(phone)):
            add_check(checks, "Valid", "Phone format", str(phone))
        else:
            add_check(checks, "Error", "Phone format", f"Phone does not have 7–15 digits: {phone}")

    date_field_names = {
        "Invoice": "Invoice Date",
        "Receipt": "Date",
        "Certificate": "Issue Date",
        "Application Form": "Application Date",
        "Report": "Date",
    }
    date_field = date_field_names.get(document_type)
    date = fields.get(date_field) if date_field else None
    if date_field and not is_missing(date):
        if valid_date(str(date)):
            add_check(checks, "Valid", "Date format", str(date))
        else:
            add_check(checks, "Error", "Date format", f"Date could not be validated: {date}")

    amount_field = "Total Amount" if document_type in {"Invoice", "Receipt"} else None
    amount = fields.get(amount_field) if amount_field else None
    if amount_field and not is_missing(amount):
        if valid_amount(str(amount)):
            add_check(checks, "Valid", "Numerical amount", str(amount))
        else:
            add_check(checks, "Error", "Numerical amount", f"Invalid amount: {amount}")

    for duplicate in analysis.get("duplicate_information", []):
        add_check(checks, "Warning", "Duplicate or repeated information", str(duplicate))
    for unusual in analysis.get("unusual_values", []):
        add_check(checks, "Error", "Unusual or inconsistent value", str(unusual))

    counts = {
        "valid": sum(check["status"] == "Valid" for check in checks),
        "warnings": sum(check["status"] == "Warning" for check in checks),
        "errors": sum(check["status"] == "Error" for check in checks),
    }

    if counts["errors"]:
        overall_status = "Error"
    elif counts["warnings"]:
        overall_status = "Warning"
    else:
        overall_status = "Valid" if document_type != "General Document" or checks else "Valid"

    return {
        "overall_status": overall_status,
        "checks": checks,
        "valid_count": counts["valid"],
        "warning_count": counts["warnings"],
        "error_count": counts["errors"],
        "disclaimer": "This status reports implemented rule-based checks only; it does not confirm legal authenticity.",
    }
