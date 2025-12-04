from io import BytesIO
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from .schema import Invoice


def _fmt_currency(amount: Optional[float], currency: Optional[str]) -> str:
    if amount is None:
        return "-"
    if not currency:
        return f"{amount:,.2f}"
    currency = currency.upper()
    symbol_map = {"EUR": "€", "INR": "₹", "USD": "$"}
    symbol = symbol_map.get(currency, "")
    return f"{symbol} {amount:,.2f}".strip()


def build_invoice_story(invoice: Invoice, status: Optional[bool] = None) -> List:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
        )
    )

    story: List = []

    # Title
    story.append(Paragraph("Invoice QC Report", styles["Title"]))
    story.append(Spacer(1, 6 * mm))

    # Top row: invoice + status
    invoice_id = invoice.get_invoice_id()
    status_label = "-"
    status_bg = colors.whitesmoke
    if status is True:
        status_label = "valid"
        status_bg = colors.HexColor("#b6f2b5")  # green-ish
    elif status is False:
        status_label = "invalid"
        status_bg = colors.HexColor("#ffb3b3")  # red-ish

    header_data = [["Invoice ID", "Buyer", "Seller", "Invoice Date", "Gross Total", "Status"]]
    header_data.append(
        [
            invoice_id,
            invoice.buyer_name or "",
            invoice.seller_name or "",
            invoice.invoice_date.isoformat() if invoice.invoice_date else "",
            _fmt_currency(invoice.gross_total, invoice.currency),
            status_label,
        ]
    )

    header_table = Table(
        header_data,
        colWidths=[30 * mm, 40 * mm, 40 * mm, 30 * mm, 30 * mm, 20 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (-1, 1), (-1, 1), status_bg),
            ]
        )
    )

    story.append(header_table)
    story.append(Spacer(1, 10 * mm))

    # Buyer / Seller
    buyer_lines = []
    if invoice.buyer_name:
        buyer_lines.append(f"<b>{invoice.buyer_name}</b>")
    buyer_para = Paragraph(
        "<br/>".join(buyer_lines) or "<b>Buyer</b>", styles["BodySmall"]
    )

    seller_lines = []
    if invoice.seller_name:
        seller_lines.append(f"<b>{invoice.seller_name}</b>")
    seller_para = Paragraph(
        "<br/>".join(seller_lines) or "<b>Seller</b>", styles["BodySmall"]
    )

    parties_table = Table(
        [[buyer_para, seller_para]],
        colWidths=[90 * mm, 90 * mm],
    )
    parties_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(parties_table)
    story.append(Spacer(1, 6 * mm))

    # Invoice info + totals
    info_data = [
        ["Invoice Information", ""],
        ["Invoice Number", invoice.invoice_number or invoice_id],
        ["Invoice Date", invoice.invoice_date.isoformat() if invoice.invoice_date else "-"],
    ]

    totals_data = [
        ["Currency / Totals", ""],
        ["Currency", invoice.currency or "-"],
        ["Net Total", _fmt_currency(invoice.net_total, invoice.currency)],
        ["Tax Total", _fmt_currency(invoice.tax_amount, invoice.currency)],
        ["Gross Total", _fmt_currency(invoice.gross_total, invoice.currency)],
    ]

    info_table = Table(info_data, colWidths=[40 * mm, 50 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (1, 0)),
                ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )

    totals_table = Table(totals_data, colWidths=[40 * mm, 50 * mm])
    totals_table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (1, 0)),
                ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )

    two_col = Table([[info_table, totals_table]], colWidths=[90 * mm, 90 * mm])
    two_col.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

    story.append(two_col)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Line items not included in this version.", styles["BodySmall"]))

    return story


def create_invoice_pdf_file(invoice: Invoice, filename: str, status: Optional[bool] = None) -> None:
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    story = build_invoice_story(invoice, status=status)
    doc.build(story)


def create_invoice_pdf_bytes(invoice: Invoice, status: Optional[bool] = None) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    story = build_invoice_story(invoice, status=status)
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
