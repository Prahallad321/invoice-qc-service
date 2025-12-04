import argparse
import json
import sys
from pathlib import Path
from typing import List

from .extractor import extract_invoices_from_dir
from .validator import validate_invoices
from .pdf_generator import create_invoice_pdf_file
from .schema import Invoice


def cmd_run(args: argparse.Namespace) -> int:
    pdf_dir = args.pdf_dir
    json_out = Path(args.json_out)
    pdf_out_dir = Path(args.pdf_out_dir)

    pdf_out_dir.mkdir(parents=True, exist_ok=True)

    invoices: List[Invoice] = extract_invoices_from_dir(pdf_dir)
    validation = validate_invoices(invoices)

    payload = {
        "extracted": [i.dict() for i in invoices],
        "validation": validation,
    }

    json_out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Saved reports.json → {json_out}")

    valid_map = {
        r["invoice_id"]: r["is_valid"] for r in validation["results"]
    }

    for inv in invoices:
        inv_id = inv.get_invoice_id()
        is_valid = valid_map.get(inv_id)
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in inv_id)
        out_pdf = pdf_out_dir / f"{safe_id}.pdf"
        create_invoice_pdf_file(inv, str(out_pdf), status=is_valid)
        label = "VALID" if is_valid else "INVALID"
        print(f"  - {label}: {out_pdf}")

    s = validation["summary"]
    print("\nSummary:")
    print(f"  Total   : {s['total_invoices']}")
    print(f"  Valid   : {s['valid_invoices']}")
    print(f"  Invalid : {s['invalid_invoices']}")

    return 1 if s["invalid_invoices"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Invoice QC CLI: Extract + Validate + PDF reports"
    )
    parser.add_argument("--pdf-dir", required=True, help="Directory with PDF invoices")
    parser.add_argument(
        "--json-out", default="reports.json", help="Output JSON report file"
    )
    parser.add_argument(
        "--pdf-out-dir",
        default="invoice_reports",
        help="Directory for per-invoice PDF reports",
    )
    parser.set_defaults(func=cmd_run)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

