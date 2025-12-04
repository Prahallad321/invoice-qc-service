from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile

import json

from .extractor import extract_invoice_from_file
from .schema import Invoice
from .validator import validate_invoices
from .pdf_generator import create_invoice_pdf_bytes

app = FastAPI(title="Invoice QC Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract-and-validate-pdfs")
async def extract_and_validate_pdfs(files: List[UploadFile] = File(...)):
    invoices: List[Invoice] = []

    for f in files:
        inv = extract_invoice_from_file(f.file, f.filename)
        invoices.append(inv)

    validation = validate_invoices(invoices)

    payload = {
        "extracted": [i.dict() for i in invoices],
        "validation": validation,
    }

    Path("reports.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )

    return payload


@app.post("/validate-json")
async def validate_json(invoices: List[Invoice]):
    validation = validate_invoices(invoices)
    return validation


@app.post("/generate-report-pdf")
async def generate_report_pdf(invoice: Invoice, is_valid: bool | None = None):
    pdf_bytes = create_invoice_pdf_bytes(invoice, status=is_valid)
    return {
        "invoice_id": invoice.get_invoice_id(),
        "pdf_hex": pdf_bytes.hex(),
    }
