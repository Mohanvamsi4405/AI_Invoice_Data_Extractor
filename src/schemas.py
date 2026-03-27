from pydantic import BaseModel
from typing import Optional, List


class LineItem(BaseModel):
    description: Optional[str] = None
    hsn_sac_code: Optional[str] = None
    quantity: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[str] = None
    discount: Optional[str] = None
    amount: Optional[str] = None

    class Config:
        extra = "ignore"


class InvoiceData(BaseModel):
    # ── Mandatory ─────────────────────────────────────────
    invoice_number:     Optional[str] = None
    invoice_date:       Optional[str] = None
    vendor_name:        Optional[str] = None
    customer_name:      Optional[str] = None
    total_amount:       Optional[str] = None
    line_items:         Optional[List[LineItem]] = None   # Item Details

    # ── Dates ─────────────────────────────────────────────
    due_date:           Optional[str] = None
    delivery_date:      Optional[str] = None

    # ── Vendor Info ───────────────────────────────────────
    vendor_address:     Optional[str] = None
    vendor_gstin:       Optional[str] = None
    vendor_pan:         Optional[str] = None
    vendor_email:       Optional[str] = None
    vendor_phone:       Optional[str] = None
    vendor_bank_details: Optional[str] = None

    # ── Customer Info ─────────────────────────────────────
    customer_address:   Optional[str] = None
    customer_gstin:     Optional[str] = None
    customer_contact:   Optional[str] = None

    # ── Financial ─────────────────────────────────────────
    subtotal:           Optional[str] = None
    discount_overall:   Optional[str] = None
    shipping_charges:   Optional[str] = None
    cgst:               Optional[str] = None
    sgst:               Optional[str] = None
    igst:               Optional[str] = None
    round_off:          Optional[str] = None
    currency:           Optional[str] = None

    # ── Payment ───────────────────────────────────────────
    payment_method:     Optional[str] = None
    transaction_id:     Optional[str] = None
    payment_date:       Optional[str] = None
    payment_status:     Optional[str] = None

    # ── Compliance ────────────────────────────────────────
    place_of_supply:    Optional[str] = None
    reverse_charge:     Optional[str] = None
    notes:              Optional[str] = None

    class Config:
        extra = "ignore"


class InvoiceResponse(BaseModel):
    success: bool
    filename: str
    extracted_text_length: int
    invoice_data: Optional[InvoiceData] = None
    error: Optional[str] = None
    processing_steps: List[str] = []
    saved_to_excel: bool = False
    excel_row: Optional[int] = None
