# Invoice QC Service

## Overview

**Invoice QC Service** is an end-to-end invoice document processing pipeline that:

- Extracts structured data from PDF invoices using regex and heuristics  
- Validates extracted data using well-defined Quality Control (QC) rules  
- Produces a consolidated JSON report (`reports.json`)  
- Generates stylized PDF invoice reports (VALID / INVALID)  
- Provides:
  - A batch **CLI** interface
  - A **FastAPI** backend service
  - A **Streamlit** web console for upload, validation & downloads

This project simulates a practical internal QC tool used in automated finance workflows.

---

## Architecture

```

PDF Upload (Streamlit or CLI)
        ↓
PDF Text Extraction (pdfplumber)
        ↓
Regex + Heuristic Field Parsing
        ↓
Pydantic Invoice Schema
        ↓
QC Validation Rules
        ↓
reports.json
        ↓
PDF Report Generator (ReportLab)
        ↓
Download via Streamlit
 API PDF endpoint
```

## Folder Structure

```

Invoice_qc_service/
│
├── invoice_qc/
│   ├── __init__.py
│   ├── schema.py           # Pydantic invoice & line item models
│   ├── extractor.py       # PDF → structured Invoice objects
│   ├── validator.py       # Quality Control rules
│   ├── pdf_generator.py  # Styled Invoice PDF generation
│   ├── api.py             # FastAPI server
│   └── cli.py             # CLI tool
│
├── streamlit_app.py       # Streamlit QC Console
├── pdfs/                  # Saved uploaded PDFs
├── invoice_reports/      # Generated invoice PDF files
├── reports.json          # JSON output from validations
├── requirements.txt
└── README.md
```




---

## Invoice Schema

Each PDF is normalized into a Pydantic model.

### Core Fields

| Field | Description |
|------|---------------|
| `source_pdf` | Original file name |
| `invoice_number` | Unique invoice reference |
| `seller_name` | Seller company name |
| `buyer_name` | Buyer company name |
| `invoice_date` | Issue date |
| `currency` | ISO currency code |
| `net_total` | Pre-tax amount |
| `tax_amount` | VAT / GST tax |
| `gross_total` | Final total |

### Line Items (optional)

| Field | Description |
|-------|---------------|
| `description` | Item name |
| `quantity` | Units |
| `unit_price` | Price per unit |
| `line_total` | Item total |

---

## Validation Rules

### 1. Completeness Rules

- `invoice_number` must exist  
- `buyer_name` must exist  
- `seller_name` must exist  
- `invoice_date` must exist  
- `gross_total` must exist  

---

### 2. Formatting Rules

- `invoice_date` must be parseable  
- Currency must be supported (EUR, USD, INR)  
- Monetary values must be numeric and positive

---

### 3. Business Rules

- `net_total + tax_amount ≈ gross_total`
- Negative totals are invalid

---

### 4. Anomaly Detection

- Duplicate `invoice_number`
- Invoice date range sanity check

---

## CLI Usage

### Install

```bash
pip install -r requirements.txt
```

## JSON Report Example

```bash
{
  "invoice_number": "AUFNR234953",
  "buyer_name": "Example AG",
  "seller_name": "JKL Corporation",
  "invoice_date": "2022-05-02",
  "currency": "EUR",
  "net_total": 216.00,
  "tax_amount": 41.04,
  "gross_total": 257.04
}
```

# API Usage

## Start Server

```bash
uvicorn invoice_qc.api:app --reload
```

## Streamlit UI

```bash
streamlit run streamlit_app.py
```

## Setup Steps

### Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---


## Features

-Upload multiple invoice PDFs

-Save them locally into pdfs/

-Run extraction & validation via FastAPI

-Show summary metrics and error tables

-Download validated invoice PDFs



























  


