from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str = Field(..., description="Item description")
    quantity: float = Field(..., ge=0, description="Quantity")
    unit_price: float = Field(..., ge=0, description="Unit price")
    line_total: float = Field(..., ge=0, description="Line total")


class Invoice(BaseModel):
    """
    Core invoice schema used across extractor, validator, CLI, API,
    Streamlit UI and PDF generator.
    """

    # Metadata
    source_pdf: Optional[str] = Field(
        default=None, description="Path or name of the source PDF file"
    )

    # Identifiers
    invoice_number: Optional[str] = Field(
        default=None, description="Invoice number"
    )

    # Parties
    seller_name: Optional[str] = Field(
        default=None, description="Seller name"
    )
    buyer_name: Optional[str] = Field(
        default=None, description="Buyer name"
    )

    # Dates
    invoice_date: Optional[date] = Field(
        default=None, description="Invoice date"
    )

    # Money
    currency: Optional[str] = Field(
        default=None, description="Currency code"
    )
    net_total: Optional[float] = Field(
        default=None, description="Net total"
    )
    tax_amount: Optional[float] = Field(
        default=None, description="Tax amount"
    )
    gross_total: Optional[float] = Field(
        default=None, description="Gross total"
    )

    # Line items (optional for now)
    line_items: List[LineItem] = Field(default_factory=list)

    def get_invoice_id(self) -> str:
        """
        Unified identifier used for filenames, tables, etc.
        """
        return self.invoice_number or self.source_pdf or "UNKNOWN_INVOICE"
