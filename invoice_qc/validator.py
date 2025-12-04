from collections import Counter
from typing import List, Dict

from .schema import Invoice


ALLOWED_CURRENCIES = {"INR", "USD", "EUR", "GBP"}


def validate_invoice(inv: Invoice) -> List[str]:
    errors: List[str] = []

    # Completeness
    if not inv.invoice_number:
        errors.append("missing:invoice_number")
    if not inv.invoice_date:
        errors.append("missing:invoice_date")
    if not inv.seller_name:
        errors.append("missing:seller_name")
    if not inv.buyer_name:
        errors.append("missing:buyer_name")

    # Format
    if inv.currency and inv.currency.upper() not in ALLOWED_CURRENCIES:
        errors.append(f"invalid:currency:{inv.currency}")

    for field, val in [
        ("net_total", inv.net_total),
        ("tax_amount", inv.tax_amount),
        ("gross_total", inv.gross_total),
    ]:
        if val is not None and val < 0:
            errors.append(f"invalid:negative:{field}")

    # Business rule: net + tax ≈ gross
    if inv.net_total is not None and inv.tax_amount is not None and inv.gross_total is not None:
        expected = round(inv.net_total + inv.tax_amount, 2)
        provided = round(inv.gross_total, 2)
        if abs(expected - provided) > 0.02:
            errors.append("rule:totals_mismatch")

    # Anomaly: date range sanity
    if inv.invoice_date:
        if inv.invoice_date.year < 2000 or inv.invoice_date.year > 2100:
            errors.append("anomaly:invoice_date_out_of_range")

    return errors


def validate_invoices(invoices: List[Invoice]) -> Dict:
    results = []
    error_counter = Counter()
    seen_keys = set()

    for inv in invoices:
        invoice_id = inv.get_invoice_id()

        # Duplicate detection (simple: number + date)
        dup_key = (inv.invoice_number, inv.invoice_date)
        duplicate = False
        if dup_key in seen_keys:
            duplicate = True
        else:
            seen_keys.add(dup_key)

        errors = validate_invoice(inv)
        if duplicate:
            errors.append("duplicate:invoice")

        for e in errors:
            error_counter[e] += 1

        results.append(
            {
                "invoice_id": invoice_id,
                "is_valid": not errors,
                "errors": errors,
            }
        )

    total = len(invoices)
    valid = sum(1 for r in results if r["is_valid"])

    summary = {
        "total_invoices": total,
        "valid_invoices": valid,
        "invalid_invoices": total - valid,
        "error_counts": dict(error_counter),
    }

    return {
        "results": results,
        "summary": summary,
    }

