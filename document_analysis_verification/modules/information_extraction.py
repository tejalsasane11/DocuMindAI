"""Explainable regex-based extraction of structured document fields."""

import re
from datetime import datetime
from typing import Dict, Iterable, List


NOT_FOUND = "Not Found"


def clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :-\t\r\n")


def unique_matches(matches: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(clean_value(match) for match in matches if clean_value(match)))


def extract_emails(text: str) -> List[str]:
    pattern = r"(?<![\w.-])[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])"
    return unique_matches(re.findall(pattern, text, flags=re.IGNORECASE))


def extract_phones(text: str) -> List[str]:
    labeled = re.search(
        r"(?im)^\s*(?:phone|telephone|mobile|contact(?:\s+number)?|tel\.?)\s*[:#=-]?\s*([^\n]+)",
        text,
    )
    if labeled:
        return [clean_value(labeled.group(1))]

    pattern = r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?){2,4}\d{2,5}"
    candidates = unique_matches(re.findall(pattern, text))

    cleaned = []
    for candidate in candidates:
        digits = re.sub(r"\D", "", candidate)
        if 7 <= len(digits) <= 15:
            cleaned.append(candidate)
    return cleaned


def extract_dates(text: str) -> List[str]:
    patterns = [
        r"\b(?:0?[1-9]|[12]\d|3[01])[/-](?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}\b",
        r"\b(?:19|20)\d{2}[/-](?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])\b",
        r"\b(?:0?[1-9]|[12]\d|3[01])[ -](?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[ -](?:19|20)\d{2}\b",
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[ -](?:0?[1-9]|[12]\d|3[01])[, ]+(?:19|20)\d{2}\b",
    ]

    matches: List[str] = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return unique_matches(matches)


def extract_labeled_value(text: str, labels: Iterable[str]) -> str:
    label_pattern = "|".join(re.escape(label) for label in sorted(labels, key=len, reverse=True))
    pattern = rf"(?im)^\s*(?:{label_pattern})\s*[:#=-]?\s*([^\n]+)$"
    match = re.search(pattern, text)
    return clean_value(match.group(1)) if match else NOT_FOUND


def extract_invoice_number(text: str) -> str:
    pattern = re.compile(
        r"(?im)^\s*(?:invoice|bill|receipt|certificate|application)\s*(?:number|no\.?|id)?\s*[:#=-]\s*([A-Za-z0-9][A-Za-z0-9./_-]*)"
    )
    match = pattern.search(text)
    return clean_value(match.group(1)) if match else NOT_FOUND


def normalize_amount(value: str) -> str:
    if not value:
        return NOT_FOUND
    cleaned = clean_value(value)
    cleaned = cleaned.replace("I", "", 1) if cleaned.startswith("I") else cleaned
    cleaned = cleaned.replace("₹", "")
    return cleaned


def extract_amount(text: str) -> str:
    labels = r"(?:grand\s+total|invoice\s+total|net\s+total|total\s+amount|amount\s+due|balance\s+due|paid\s+amount|subtotal|total)"
    pattern = re.compile(
        rf"(?im)^\s*{labels}\s*[:#=-]?\s*[$€£₹]?\s*(-?\d{{1,3}}(?:[,.]\d{{3}})*(?:[.,]\d{{1,2}})|-?\d+(?:[.,]\d{{1,2}})?)",
    )
    match = pattern.search(text)
    if not match:
        return NOT_FOUND

    value = clean_value(match.group(1))
    return value


def extract_address(text: str) -> str:
    pattern = re.compile(
        r"(?im)^\s*(?:address|billing address|shipping address|location)\s*[:=-]?\s*([^\n]+)",
    )
    match = pattern.search(text)
    if match:
        return clean_value(match.group(1))

    # Conservative fallback: identify a street-like line only.
    fallback = re.search(
        r"(?im)^\s*\d{1,5}\s+[A-Za-z][A-Za-z0-9 .,'-]{5,80}\s*$",
        text,
    )
    return clean_value(fallback.group(0)) if fallback else NOT_FOUND


def extract_name(text: str) -> str:
    labeled = extract_labeled_value(
        text,
        ["Customer Name", "Applicant Name", "Student Name", "Patient Name", "Name"],
    )
    if labeled != NOT_FOUND:
        return labeled

    match = re.search(
        r"(?im)^\s*(?:from|prepared by|issued to|candidate)\s*[:=-]?\s*([A-Z][A-Za-z .'-]{2,80})\s*$",
        text,
    )
    return clean_value(match.group(1)) if match else NOT_FOUND


def extract_organization(text: str) -> str:
    return extract_labeled_value(
        text,
        ["Organization", "Company", "Employer", "Institution", "Vendor", "Issuer"],
    )


def extract_keywords(text: str) -> List[str]:
    keyword_words = {
        "invoice", "receipt", "certificate", "report", "application",
        "amount", "total", "date", "email", "phone", "address",
        "payment", "student", "employee", "company", "customer",
    }
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    counts = {}
    for word in words:
        if word in keyword_words:
            counts[word] = counts.get(word, 0) + 1
    return [word for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def extract_numbers(text: str) -> List[str]:
    matches = re.findall(r"(?<![A-Za-z])(?:₹|[$€£])?\d+(?:[,.]\d+)*(?:\.\d+)?", text)
    return unique_matches(matches)


def extract_structured_information(text: str) -> Dict[str, str | List[str]]:
    """Extract common and document-specific fields without inventing values."""
    if not text or not text.strip():
        text = ""

    emails = extract_emails(text)
    phones = extract_phones(text)
    dates = extract_dates(text)

    fields: Dict[str, str | List[str]] = {
        "Person Name": extract_name(text),
        "Organization": extract_organization(text),
        "Email": emails[0] if emails else NOT_FOUND,
        "Phone": phones[0] if phones else NOT_FOUND,
        "Date": dates[0] if dates else NOT_FOUND,
        "Invoice Number": extract_invoice_number(text),
        "Amount/Total": extract_amount(text),
        "Address": extract_address(text),
        "All Emails": emails,
        "All Phones": phones,
        "All Dates": dates,
        "Keywords": extract_keywords(text),
    }

    fields.update(extract_document_specific_fields(text))
    return fields


def extract_document_specific_fields(text: str) -> Dict[str, str]:
    """Extract fields relevant to the detected document category."""
    normalized = text.lower()

    if any(marker in normalized for marker in ("application form", "application number", "applicant name", "declaration")):
        return {
            "Applicant Name": extract_labeled_value(text, ["Applicant Name", "Student Name", "Name"]),
            "Organization": extract_organization(text),
            "Email": (extract_emails(text)[0] if extract_emails(text) else NOT_FOUND),
            "Phone": (extract_phones(text)[0] if extract_phones(text) else NOT_FOUND),
            "Address": extract_address(text),
            "Application Date": extract_labeled_value(text, ["Application Date", "Date"]),
            "Application Number": extract_labeled_value(text, ["Application Number"]),
        }

    if any(marker in normalized for marker in ("certificate", "certify", "awarded", "certificate number")):
        return {
            "Certificate ID": extract_labeled_value(text, ["Certificate Number", "Certificate ID", "Certificate No"]),
            "Person Name": extract_labeled_value(text, ["Student Name", "Person Name", "Name"]),
            "Institution Name": extract_labeled_value(text, ["Institution", "Organization", "Issuer"]),
            "Certificate Type": extract_labeled_value(text, ["Course", "Certificate Type"]),
            "Issue Date": extract_labeled_value(text, ["Issue Date", "Date"]),
        }

    if any(marker in normalized for marker in ("receipt", "paid amount", "payment received", "change due")):
        return {
            "Receipt Number": extract_labeled_value(text, ["Receipt Number", "Receipt No"]),
            "Shop Name": extract_labeled_value(text, ["Shop Name", "Organization", "Company", "Store"]),
            "Date": extract_labeled_value(text, ["Transaction Date", "Date"]),
            "Total Amount": normalize_amount(extract_labeled_value(text, ["Paid Amount", "Total Amount", "Amount", "Total"])),
            "Payment Method": extract_labeled_value(text, ["Payment Method", "Payment Mode"]),
            "Items": extract_labeled_value(text, ["Items", "Description"]),
        }

    if any(marker in normalized for marker in ("invoice", "invoice number", "bill to", "subtotal", "amount due")):
        return {
            "Invoice Number": extract_labeled_value(text, ["Invoice Number", "Invoice No"]),
            "Invoice Date": extract_labeled_value(text, ["Invoice Date", "Date"]),
            "Seller Name": extract_labeled_value(text, ["Organization", "Seller", "Vendor", "Issuer"]),
            "Customer Name": extract_labeled_value(text, ["Customer Name", "Applicant Name", "Name"]),
            "Email": (extract_emails(text)[0] if extract_emails(text) else NOT_FOUND),
            "Phone": (extract_phones(text)[0] if extract_phones(text) else NOT_FOUND),
            "Subtotal": normalize_amount(extract_labeled_value(text, ["Subtotal"])),
            "Tax": normalize_amount(extract_labeled_value(text, ["Tax", "VAT", "GST"])),
            "Total Amount": normalize_amount(extract_labeled_value(text, ["Total Amount", "Grand Total", "Amount Due", "Total"])),
        }

    if any(marker in normalized for marker in ("report", "findings", "conclusion", "summary", "analysis")):
        title_match = re.search(r"(?im)^\s*(?:report title|title)\s*[:=-]?\s*([^\n]+)", text)
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return {
            "Report Title": clean_value(title_match.group(1)) if title_match else clean_value(first_line),
            "Organization": extract_organization(text),
            "Date": extract_labeled_value(text, ["Report Date", "Date"]),
            "Keywords": extract_keywords(text),
            "Numerical Information": extract_numbers(text),
        }

    return {
        "Extracted Text Summary": clean_value(text[:300]) if text else NOT_FOUND,
        "Email": (extract_emails(text)[0] if extract_emails(text) else NOT_FOUND),
        "Phone": (extract_phones(text)[0] if extract_phones(text) else NOT_FOUND),
        "Date": (extract_dates(text)[0] if extract_dates(text) else NOT_FOUND),
    }
