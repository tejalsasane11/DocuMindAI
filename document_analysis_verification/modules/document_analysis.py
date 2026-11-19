"""Simple and explainable document analysis functions."""

import re
from collections import Counter
from typing import Dict, List


NOT_FOUND = "Not Found"

DOCUMENT_TYPES = {
    "Invoice": ["invoice", "gst", "vat", "bill to", "amount due", "seller", "invoice number", "subtotal", "tax"],
    "Receipt": ["receipt", "payment received", "cash received", "change due", "paid amount", "payment method", "shop"],
    "Certificate": ["certificate", "certify", "certified", "awarded", "achievement", "certificate number", "institution"],
    "Application Form": ["application form", "application number", "applicant", "candidate", "declaration", "student application"],
    "Report": ["project report", "completion report", "report number", "findings", "conclusion", "summary", "analysis"],
}

REQUIRED_FIELDS_BY_TYPE = {
    "Invoice": ["Invoice Number", "Date", "Customer Name", "Total Amount"],
    "Receipt": ["Receipt Number", "Shop Name", "Date", "Total Amount"],
    "Certificate": ["Certificate ID", "Person Name", "Institution Name", "Issue Date"],
    "Application Form": ["Applicant Name", "Email", "Phone", "Address", "Application Date"],
    "Report": ["Report Title", "Organization", "Date"],
    "General Document": [],
}


def detect_document_type(text: str) -> str:
    """Classify a document using weighted, unique keyword matches."""
    normalized = " " + re.sub(r"[^a-z0-9]+", " ", text.lower()) + " "
    scores = {}

    for document_type, keywords in DOCUMENT_TYPES.items():
        score = 0
        for keyword in keywords:
            clean_keyword = re.sub(r"[^a-z0-9]+", " ", keyword).strip()
            if clean_keyword in normalized:
                weight = 3 if " " in clean_keyword or clean_keyword.endswith("number") else 1
                score += weight
        scores[document_type] = score

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best_type, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    if best_score == 0:
        return "General Document"
    if best_score < 2 or best_score == second_score:
        return "General Document"
    return best_type


def find_missing_fields(fields: Dict[str, object], document_type: str) -> List[str]:
    """Return required fields whose values are missing or unusable."""
    required_fields = REQUIRED_FIELDS_BY_TYPE.get(document_type, REQUIRED_FIELDS_BY_TYPE["General Document"])
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
