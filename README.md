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

## Invoice Schema

- Each invoice is normalized into the following structure using Pydantic models.

  ### Invoice Model

```
| Field            | Description                            |
| ---------------- | -------------------------------------- |
| `source_pdf`     | Original PDF filename                  |
| `invoice_number` | Unique invoice identifier              |
| `seller_name`    | Company issuing the invoice            |
| `buyer_name`     | Recipient / customer company           |
| `invoice_date`   | Invoice issue date                     |
| `currency`       | ISO currency code (EUR, USD, INR etc.) |
| `net_total`      | Pre-tax amount                         |
| `tax_amount`     | VAT/GST amount                         |
| `gross_total`    | Total payable amount                   |
| `line_items[]`   | Optional item rows                     |
```

### Line Item Model

```
| Field         | Description             |
| ------------- | ----------------------- |
| `description` | Product or service name |
| `quantity`    | Number of units         |
| `unit_price`  | Price per unit          |
| `line_total`  | Row total               |
```
## Validation Rules

- The QC Validator applies multiple categories of rules:
  
  ### 1. Completeness Rules

  ```
  
  Rule
| ---------------------------------- |
| `invoice_number` must not be empty |
| `seller_name` must not be empty    |
| `buyer_name` must not be empty     |
| `invoice_date` must not be empty   |
| `gross_total` must not be empty    |
```
  





























  


