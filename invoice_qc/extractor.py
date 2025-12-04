import re
from datetime import datetime
from pathlib import Path
from typing import IO, List, Optional

import pdfplumber
from .schema import Invoice

# -------------------- Utilities --------------------

DATE_PATTERN = r"(\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})"


def parse_date(value: str):
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except:
            pass
    return None


def parse_amount(text: str) -> Optional[float]:
    """
    Convert € 1.234,56 or 1234,56 or 1234.56 to float.
    """
    text = text.replace("EUR", "").replace("€", "").strip()

    # European format fix
    if "," in text:
        text = text.replace(".", "")
        text = text.replace(",", ".")

    try:
        return float(text)
    except:
        return None


def normalize_name(value: str) -> str:
    """
    Try to isolate a company name: remove trailing noise words.
    """
    value = value.replace("\n", " ").strip()
    junk_tokens = ["bestellung", "auftrag", "fax", "tel", "vom", "im auftrag von"]
    for t in junk_tokens:
        value = value.lower().split(t)[0]
    return value.title().strip()


# -------------------- Extractors --------------------

def extract_invoice_number(text: str):

    m = re.search(r"(AUFNR\d+)", text)
    return m.group(1) if m else None


def extract_invoice_date(text: str):
    m = re.search(r"Bestellung\s+AUFNR\d+.*?vom\s+" + DATE_PATTERN, text)
    return parse_date(m.group(1)) if m else None


def extract_buyer(text: str) -> Optional[str]:
    """
    Assume buyer block occurs BEFORE address line containing 'Deutschland'.
    Capture first firm-like line before it.
    """

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        if "deutschland" in line.lower() or re.search(r"\b[0-9]{5}\b", line):
            if i > 0:
                return normalize_name(lines[i - 1])

    return None


def extract_seller(text: str) -> Optional[str]:

    m = re.search(r"\n([A-Za-z\s]+(?:Corporation|GmbH|Ltd))", text)
    
    if m:
        return normalize_name(m.group(1))

    # fallback scan for known forms
    name_match = re.search(r"\b([A-Za-z ]{4,40}(?:Corporation|GmbH|Ltd))\b", text)
    return normalize_name(name_match.group(1)) if name_match else None


def extract_currency(text: str):
    if "EUR" in text or "€" in text:
        return "EUR"
    return None


def extract_totals(text: str):
    """
    Flex parsing totals with line scanning.
    """

    net = tax = gross = None

    for line in text.splitlines():

        lower = line.lower()
        numbers = re.findall(r"[€]?\s*[\d.,]+", line)

        if not numbers:
            continue

        value = parse_amount(numbers[-1])

        if not value:
            continue

        if any(k in lower for k in ["netto", "net total", "net amount", "subtotal"]):
            net = value

        elif any(k in lower for k in ["mwst", "tax", "vat", "gst"]):
            tax = value

        elif any(k in lower for k in ["gesamt", "gross", "total"]):
            gross = value

    return net, tax, gross


# -------------------- Pipeline --------------------

def extract_invoice_from_file(file: IO, filename: str) -> Invoice:

    with pdfplumber.open(file) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)

    inv_no = extract_invoice_number(text)
    inv_date = extract_invoice_date(text)
    buyer = extract_buyer(text)
    seller = extract_seller(text)

    currency = extract_currency(text)

    net, tax, gross = extract_totals(text)

    return Invoice(
        source_pdf=filename,
        invoice_number=inv_no,
        invoice_date=inv_date,
        buyer_name=buyer,
        seller_name=seller,
        currency=currency,
        net_total=net,
        tax_amount=tax,
        gross_total=gross,
        line_items=[],
    )


def extract_invoices_from_dir(folder: str) -> List[Invoice]:

    invoices = []

    for f in Path(folder).glob("*.pdf"):
        with open(f, "rb") as fh:
            invoices.append(extract_invoice_from_file(fh, f.name))

    return invoices
