"""
Generate a comprehensive test invoice PDF covering ALL extraction fields.
Run: python generate_test_invoice.py
Output: test_invoice_full.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

W, H = A4
OUT = "test_invoice_full.pdf"

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#1E3A5F")
BLUE    = colors.HexColor("#2563EB")
AMBER   = colors.HexColor("#F59E0B")
GREEN   = colors.HexColor("#059669")
LGREY   = colors.HexColor("#F1F5F9")
MGREY   = colors.HexColor("#94A3B8")
WHITE   = colors.white
BLACK   = colors.HexColor("#1E293B")

styles  = getSampleStyleSheet()

def S(name, **kw):
    base = styles[name] if name in styles else styles["Normal"]
    return ParagraphStyle(name + str(id(kw)), parent=base, **kw)

def P(text, style):
    return Paragraph(str(text), style)

def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=12*mm, bottomMargin=12*mm,
    )
    story = []

    # ── HEADER BAR ────────────────────────────────────────────────────────────
    hdr_data = [[
        P("TECHWAVE SOLUTIONS PVT. LTD.", S("Normal",
            fontSize=16, textColor=WHITE, fontName="Helvetica-Bold")),
        P("TAX INVOICE", S("Normal",
            fontSize=20, textColor=AMBER, fontName="Helvetica-Bold",
            alignment=TA_RIGHT)),
    ]]
    hdr_tbl = Table(hdr_data, colWidths=[100*mm, 80*mm])
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 4*mm))

    # ── VENDOR INFO (left) + INVOICE META (right) ─────────────────────────────
    lbl  = S("Normal", fontSize=7, textColor=MGREY, fontName="Helvetica-Bold",
              spaceAfter=1)
    val  = S("Normal", fontSize=9, textColor=BLACK, fontName="Helvetica",
              spaceAfter=2)
    val2 = S("Normal", fontSize=9, textColor=BLACK, fontName="Helvetica",
              alignment=TA_RIGHT, spaceAfter=2)
    lbl2 = S("Normal", fontSize=7, textColor=MGREY, fontName="Helvetica-Bold",
              alignment=TA_RIGHT, spaceAfter=1)

    vendor_block = [
        P("VENDOR (BILL FROM)",  lbl),
        P("TechWave Solutions Pvt. Ltd.", S("Normal", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY)),
        P("402, Sunshine Tower, BKC, Mumbai - 400051", val),
        P("Maharashtra, India", val),
        Spacer(1, 2*mm),
        P("GSTIN",               lbl),  P("27AABCT1234F1Z5", val),
        P("PAN",                 lbl),  P("AABCT1234F",      val),
        P("EMAIL",               lbl),  P("billing@techwave.in", val),
        P("PHONE",               lbl),  P("+91-98765-43210", val),
    ]

    meta_block = [
        P("INVOICE NUMBER",  lbl2), P("TWS-2025-0347",      val2),
        P("INVOICE DATE",    lbl2), P("15 March 2025",       val2),
        P("DUE DATE",        lbl2), P("30 March 2025",       val2),
        P("DELIVERY DATE",   lbl2), P("20 March 2025",       val2),
        Spacer(1, 3*mm),
        P("PLACE OF SUPPLY", lbl2), P("Maharashtra (27)",    val2),
        P("REVERSE CHARGE",  lbl2), P("No",                  val2),
        P("PAYMENT METHOD",  lbl2), P("NEFT / Bank Transfer", val2),
        P("PAYMENT STATUS",  lbl2), P("Unpaid",              val2),
    ]

    meta_tbl = Table(
        [[vendor_block, meta_block]],
        colWidths=[95*mm, 85*mm],
    )
    meta_tbl.setStyle(TableStyle([
        ("VALIGN",  (0,0), (-1,-1), "TOP"),
        ("BACKGROUND", (0,0), (0,0), LGREY),
        ("BOX",  (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ("LINEAFTER", (0,0), (0,-1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 4*mm))

    # ── BILL TO / SHIP TO ────────────────────────────────────────────────────
    cust_lbl = S("Normal", fontSize=7, textColor=WHITE, fontName="Helvetica-Bold")
    cust_val = S("Normal", fontSize=9, textColor=BLACK, fontName="Helvetica", spaceAfter=2)

    bill_cell = [
        P("BILL TO (CUSTOMER)", cust_lbl),
        Spacer(1, 1*mm),
        P("InnovateTech Enterprises Pvt. Ltd.", S("Normal", fontSize=10, fontName="Helvetica-Bold")),
        P("Plot 7, MIDC, Pune - 411018", cust_val),
        P("Maharashtra, India",             cust_val),
        P("GSTIN: 27AABCI5678G1Z3",        cust_val),
        P("Contact: Rajesh Sharma",         cust_val),
        P("Email: rajesh@innovatetech.in",  cust_val),
        P("Phone: +91-90123-45678",         cust_val),
    ]

    bank_cell = [
        P("VENDOR BANK DETAILS",            cust_lbl),
        Spacer(1, 1*mm),
        P("Bank: HDFC Bank Ltd",            cust_val),
        P("A/C No: 5020 0123 4567 89",      cust_val),
        P("IFSC: HDFC0001234",              cust_val),
        P("Branch: BKC, Mumbai",            cust_val),
        Spacer(1, 3*mm),
        P("TRANSACTION ID",                 cust_lbl),
        P("NEFT2025031500987654",           cust_val),
        P("Payment Date: 16 March 2025",    cust_val),
    ]

    bill_tbl = Table([[bill_cell, bank_cell]], colWidths=[95*mm, 85*mm])
    bill_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("TOPPADDING",    (0,0), (-1,-1), 2), ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LEFTPADDING",   (0,0), (-1,-1), 1), ("RIGHTPADDING",  (0,0), (-1,-1), 1),
    ]))

    bill_wrap = Table([[bill_cell, bank_cell]], colWidths=[95*mm, 85*mm])
    bill_wrap.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("BACKGROUND", (0,1), (-1,-1), WHITE),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ("LINEAFTER", (0,0), (0,-1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("VALIGN",  (0,0), (-1,-1), "TOP"),
    ]))
    story.append(bill_wrap)
    story.append(Spacer(1, 5*mm))

    # ── LINE ITEMS TABLE ─────────────────────────────────────────────────────
    th = S("Normal", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
           alignment=TA_CENTER)
    td = S("Normal", fontSize=8, textColor=BLACK, fontName="Helvetica")
    tdr = S("Normal", fontSize=8, textColor=BLACK, fontName="Helvetica",
            alignment=TA_RIGHT)
    tdc = S("Normal", fontSize=8, textColor=BLACK, fontName="Helvetica",
            alignment=TA_CENTER)

    items_data = [
        [P(t, th) for t in [
            "#", "Description of Services / Goods",
            "HSN/SAC", "Qty", "Unit", "Unit Price", "Discount", "Amount"
        ]],
        [
            P("1", tdc),
            P("Software Development — ERP Module (Phase 2)", td),
            P("998314", tdc), P("1", tdc), P("Project", tdc),
            P("₹60,000.00", tdr), P("₹0.00", tdr), P("₹60,000.00", tdr),
        ],
        [
            P("2", tdc),
            P("Cloud Hosting & DevOps Setup (AWS)", td),
            P("998315", tdc), P("3", tdc), P("Months", tdc),
            P("₹8,000.00", tdr), P("₹500.00", tdr), P("₹23,500.00", tdr),
        ],
        [
            P("3", tdc),
            P("UI/UX Design — Mobile App Screens (50 screens)", td),
            P("998316", tdc), P("50", tdc), P("Screens", tdc),
            P("₹500.00", tdr), P("5%", tdr), P("₹23,750.00", tdr),
        ],
        [
            P("4", tdc),
            P("Annual Software Maintenance Contract (AMC)", td),
            P("998317", tdc), P("1", tdc), P("Year", tdc),
            P("₹15,000.00", tdr), P("₹0.00", tdr), P("₹15,000.00", tdr),
        ],
        [
            P("5", tdc),
            P("Training & Onboarding (2 days on-site)", td),
            P("998318", tdc), P("2", tdc), P("Days", tdc),
            P("₹5,000.00", tdr), P("₹0.00", tdr), P("₹10,000.00", tdr),
        ],
    ]

    col_w = [8*mm, 60*mm, 18*mm, 10*mm, 14*mm, 22*mm, 18*mm, 22*mm]
    items_tbl = Table(items_data, colWidths=col_w, repeatRows=1)
    items_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("BACKGROUND",    (0,2), (-1,2),  LGREY),
        ("BACKGROUND",    (0,4), (-1,4),  LGREY),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 4*mm))

    # ── FINANCIAL SUMMARY ────────────────────────────────────────────────────
    sum_lbl = S("Normal", fontSize=9, textColor=BLACK, fontName="Helvetica")
    sum_val = S("Normal", fontSize=9, textColor=BLACK, fontName="Helvetica",
                alignment=TA_RIGHT)
    sum_bold = S("Normal", fontSize=10, textColor=NAVY, fontName="Helvetica-Bold")
    sum_bval = S("Normal", fontSize=10, textColor=NAVY, fontName="Helvetica-Bold",
                 alignment=TA_RIGHT)

    fin_data = [
        [P("Subtotal",              sum_lbl), P("₹1,32,250.00", sum_val)],
        [P("Discount (Overall)",    sum_lbl), P("- ₹2,250.00",  sum_val)],
        [P("Shipping / Freight",    sum_lbl), P("₹500.00",       sum_val)],
        [P("Taxable Amount",        sum_lbl), P("₹1,30,500.00", sum_val)],
        [P("CGST @ 9%",             sum_lbl), P("₹11,745.00",   sum_val)],
        [P("SGST @ 9%",             sum_lbl), P("₹11,745.00",   sum_val)],
        [P("IGST @ 0%",             sum_lbl), P("₹0.00",         sum_val)],
        [P("Round Off",             sum_lbl), P("- ₹0.10",       sum_val)],
        [P("GRAND TOTAL",           sum_bold), P("₹1,53,989.90", sum_bval)],
    ]

    fin_tbl = Table(fin_data, colWidths=[60*mm, 40*mm])
    fin_tbl.setStyle(TableStyle([
        ("ALIGN",         (0,0), (-1,-1), "LEFT"),
        ("GRID",          (0,0), (-1,-2), 0.3, colors.HexColor("#E2E8F0")),
        ("LINEABOVE",     (0,-1), (-1,-1), 1.5, NAVY),
        ("LINEBELOW",     (0,-1), (-1,-1), 1.5, NAVY),
        ("BACKGROUND",    (0,-1), (-1,-1), colors.HexColor("#EEF2FF")),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))

    # Place financial summary on the right
    layout = Table([[Spacer(1,1), fin_tbl]], colWidths=[88*mm, 92*mm])
    layout.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(layout)
    story.append(Spacer(1, 5*mm))

    # ── AMOUNT IN WORDS ──────────────────────────────────────────────────────
    story.append(P(
        "Amount in Words: <b>One Lakh Fifty-Three Thousand Nine Hundred "
        "Eighty-Nine Rupees and Ninety Paise Only</b>",
        S("Normal", fontSize=9, textColor=BLACK, borderColor=NAVY,
          borderWidth=0.5, borderPadding=6, backColor=LGREY)
    ))
    story.append(Spacer(1, 5*mm))

    # ── NOTES / TERMS ────────────────────────────────────────────────────────
    story.append(P("NOTES & PAYMENT TERMS",
        S("Normal", fontSize=8, textColor=NAVY, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 1*mm))
    notes_text = (
        "1. Payment due within 15 days of invoice date (by 30 March 2025).\n"
        "2. Please mention Invoice No. TWS-2025-0347 in payment reference.\n"
        "3. Late payment will attract 2% interest per month after due date.\n"
        "4. Goods once delivered will not be taken back unless defective.\n"
        "5. All disputes subject to Mumbai jurisdiction only.\n"
        "6. This is a computer-generated invoice and does not require a physical signature."
    )
    story.append(P(notes_text,
        S("Normal", fontSize=8, textColor=BLACK, leading=13)))
    story.append(Spacer(1, 5*mm))

    # ── SIGNATURE AREA ───────────────────────────────────────────────────────
    sig_data = [[
        P("Customer Acknowledgement\n\n\n\n__________________________\nSignature & Stamp",
          S("Normal", fontSize=8, textColor=BLACK, alignment=TA_CENTER)),
        Spacer(1,1),
        P("For TechWave Solutions Pvt. Ltd.\n\n\n\n__________________________\nAuthorised Signatory",
          S("Normal", fontSize=8, textColor=BLACK, alignment=TA_CENTER)),
    ]]
    sig_tbl = Table(sig_data, colWidths=[75*mm, 30*mm, 75*mm])
    sig_tbl.setStyle(TableStyle([
        ("BOX",  (0,0), (0,0),  0.5, MGREY),
        ("BOX",  (2,0), (2,0),  0.5, MGREY),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 4*mm))

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MGREY))
    story.append(Spacer(1, 2*mm))
    story.append(P(
        "TechWave Solutions Pvt. Ltd.  |  402 Sunshine Tower, BKC, Mumbai - 400051  |  "
        "billing@techwave.in  |  +91-98765-43210  |  www.techwave.in  |  "
        "CIN: U72900MH2018PTC309876",
        S("Normal", fontSize=7, textColor=MGREY, alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"Generated: {OUT}")


if __name__ == "__main__":
    build()
