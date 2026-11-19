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
        normalized = re.sub(r"[$€£₹, ]", "", value.strip())
        number = float(normalized)
        return number >= 0
    except (TypeError, ValueError):
        return False


def verify_document(fields: Dict[str, object], analysis: Dict[str, object]) -> Dict[str, object]:
    """Run rule-based checks and summarize Valid, Warning, and Error results."""
    checks: List[Dict[str, str]] = []

    required_fields = {
        "Invoice": ["Person Name", "Organization", "Email", "Phone", "Date", "Invoice Number", "Amount/Total"],
        "Receipt": ["Person Name", "Organization", "Date", "Invoice Number", "Amount/Total"],
        "Certificate": ["Person Name", "Organization", "Date"],
        "Application Form": ["Person Name", "Organization", "Email", "Phone", "Address"],
        "Report": ["Organization", "Date"],
        "Other Document": ["Person Name", "Organization", "Date"],
    }

    document_type = str(analysis.get("document_type", "Other Document"))
    for field_name in required_fields.get(document_type, required_fields["Other Document"]):
        value = fields.get(field_name)
        if is_missing(value):
            add_check(checks, "Warning", f"Required field: {field_name}", "Information is missing.")
        else:
            add_check(checks, "Valid", f"Required field: {field_name}", "Information is present.")

    email = fields.get("Email")
    if not is_missing(email):
        if valid_email(str(email)):
            add_check(checks, "Valid", "Email format", str(email))
        else:
            add_check(checks, "Error", "Email format", f"Invalid email address: {email}")

    phone = fields.get("Phone")
    if not is_missing(phone):
        if valid_phone(str(phone)):
            add_check(checks, "Valid", "Phone format", str(phone))
        else:
            add_check(checks, "Error", "Phone format", f"Phone does not have 7–15 digits: {phone}")

    date = fields.get("Date")
    if not is_missing(date):
        if valid_date(str(date)):
            add_check(checks, "Valid", "Date format", str(date))
        else:
            add_check(checks, "Error", "Date format", f"Date could not be validated: {date}")

    amount = fields.get("Amount/Total")
    if not is_missing(amount):
        if valid_amount(str(amount)):
            add_check(checks, "Valid", "Numerical amount", str(amount))
        else:
            add_check(checks, "Error", "Numerical amount", f"Invalid amount: {amount}")

    for duplicate in analysis.get("duplicate_information", []):
        add_check(checks, "Warning", "Duplicate or repeated information", str(duplicate))

    for unusual in analysis.get("unusual_values", []):
        add_check(checks, "Error", "Unusual or inconsistent value", str(unusual))

    if not str(fields.get("Invoice Number", "")).strip() or str(fields.get("Invoice Number", "")).lower() == NOT_FOUND.lower():
        add_check(checks, "Warning", "Invoice or document identifier", "Identifier is missing.")

    counts = {
        "valid": sum(check["status"] == "Valid" for check in checks),
        "warnings": sum(check["status"] == "Warning" for check in checks),
        "errors": sum(check["status"] == "Error" for check in checks),
    }

    if counts["errors"] > 0:
        overall_status = "Error"
    elif counts["warnings"] > 0:
        overall_status = "Warning"
    else:
        overall_status = "Valid"

    return {
        "overall_status": overall_status,
        "checks": checks,
        "valid_count": counts["valid"],
        "warning_count": counts["warnings"],
        "error_count": counts["errors"],
        "disclaimer": "This status reports implemented rule-based checks only; it does not confirm legal authenticity.",
    }
