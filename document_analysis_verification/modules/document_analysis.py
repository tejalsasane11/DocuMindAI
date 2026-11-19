"""Simple and explainable document analysis functions."""

import re
from collections import Counter
from typing import Dict, List


NOT_FOUND = "Not Found"

DOCUMENT_TYPES = {
    "Invoice": ["invoice", "gst", "vat", "bill to", "amount due", "invoice number"],
    "Receipt": ["receipt", "cash received", "payment received", "change due"],
    "Certificate": ["certificate", "certify", "awarded", "certified", "achievement"],
    "Application Form": ["application", "applicant", "candidate", "declaration"],
    "Report": ["report", "findings", "summary", "conclusion", "analysis"],
}

REQUIRED_FIELDS_BY_TYPE = {
    "Invoice": ["Person Name", "Organization", "Email", "Phone", "Date", "Invoice Number", "Amount/Total"],
    "Receipt": ["Person Name", "Organization", "Date", "Invoice Number", "Amount/Total"],
    "Certificate": ["Person Name", "Organization", "Date"],
    "Application Form": ["Person Name", "Organization", "Email", "Phone", "Address"],
    "Report": ["Organization", "Date"],
    "Other Document": ["Person Name", "Organization", "Date"],
}


def detect_document_type(text: str) -> str:
    """Classify a document using weighted keyword matches."""
    normalized = text.lower()
    scores = {}

    for document_type, keywords in DOCUMENT_TYPES.items():
        score = sum(normalized.count(keyword) for keyword in keywords)
        scores[document_type] = score

    best_type = max(scores, key=scores.get)
    if scores[best_type] == 0:
        return "Other Document"
    return best_type


def find_missing_fields(fields: Dict[str, object], document_type: str) -> List[str]:
    """Return required fields whose values are missing or unusable."""
    required_fields = REQUIRED_FIELDS_BY_TYPE.get(document_type, REQUIRED_FIELDS_BY_TYPE["Other Document"])
    missing = []

    for field in required_fields:
        value = fields.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and (not value.strip() or value.strip().lower() == NOT_FOUND.lower()):
            missing.append(field)
        elif isinstance(value, (list, tuple, set)) and len(value) == 0:
            missing.append(field)

    return missing


def find_duplicate_values(fields: Dict[str, object]) -> List[str]:
    """Detect repeated email, phone, and date values."""
    duplicates = []

    for field_name in ("All Emails", "All Phones", "All Dates"):
        values = fields.get(field_name, [])
        if not isinstance(values, list):
            continue

        normalized_values = [str(value).strip().lower() for value in values if str(value).strip()]
        repeated = [value for value, count in Counter(normalized_values).items() if count > 1]
        if repeated:
            duplicates.append(f"Duplicate {field_name.replace('All ', '')}: {', '.join(repeated)}")

    return duplicates


def extract_unique_keywords(text: str, limit: int = 12) -> List[str]:
    """Identify common meaningful words without external NLP libraries."""
    stop_words = {
        "the", "and", "for", "with", "from", "this", "that", "have", "has",
        "are", "was", "were", "your", "our", "will", "shall", "not", "to",
        "of", "in", "on", "at", "by", "as", "or", "be", "it", "is",
    }

    words = re.findall(r"\b[A-Za-z][A-Za-z'-]{3,}\b", text.lower())
    counts = Counter(word for word in words if word not in stop_words)
    return [word for word, _ in counts.most_common(limit)]


def detect_unusual_amounts(fields: Dict[str, object]) -> List[str]:
    """Flag implausible or conflicting numeric amount formats."""
    issues = []
    amount = fields.get("Amount/Total", NOT_FOUND)

    if not isinstance(amount, str) or amount == NOT_FOUND:
        return issues

    normalized = amount.replace("$", "").replace("€", "").replace("£", "").replace("₹", "")
    normalized = normalized.replace(",", "").strip()

    try:
        number = float(normalized)
        if number < 0:
            issues.append("Amount/Total is negative.")
        elif number == 0:
            issues.append("Amount/Total is zero.")
        elif number > 10_000_000:
            issues.append("Amount/Total is unusually large.")
    except ValueError:
        issues.append("Amount/Total does not contain a valid numeric value.")

    return issues


def analyze_document(text: str, fields: Dict[str, object]) -> Dict[str, object]:
    """Produce a simple document analysis summary."""
    document_type = detect_document_type(text)
    missing_fields = find_missing_fields(fields, document_type)
    duplicates = find_duplicate_values(fields)
    unusual_values = detect_unusual_amounts(fields)
    keywords = extract_unique_keywords(text)

    issues = []
    if missing_fields:
        issues.append("Missing required fields: " + ", ".join(missing_fields))
    issues.extend(duplicates)
    issues.extend(unusual_values)

    return {
        "document_type": document_type,
        "missing_fields": missing_fields,
        "duplicate_information": duplicates,
        "unusual_values": unusual_values,
        "keywords": keywords,
        "detected_issues": issues,
        "text_length": len(text.strip()),
        "summary": (
            f"Detected document type: {document_type}. "
            f"Missing fields: {len(missing_fields)}. "
            f"Duplicate or unusual findings: {len(duplicates) + len(unusual_values)}."
        ),
    }
