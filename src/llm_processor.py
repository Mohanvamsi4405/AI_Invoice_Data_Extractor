"""
LLM processing — LangChain + ChatGroq.
Extracts all invoice fields from raw text.
"""

import json
import logging
import re
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from .schemas import InvoiceData, LineItem

Optional_str = Optional[str]

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a world-class invoice data extraction AI used in production financial systems.

Your ONLY task: read the invoice text and return a single valid JSON object.

## STRICT OUTPUT RULES
1. Return ONLY raw JSON — no markdown, no code fences (```), no explanation text.
2. All scalar values must be strings or null. Never return bare numbers or booleans.
3. Amounts: preserve original formatting with currency symbol (e.g. "₹1,20,000.00", "$4,500.00").
4. Dates: convert to YYYY-MM-DD. If year is ambiguous, infer from context.
5. vendor_name = the company/person who ISSUED the invoice (look for letterhead, "From:", "Sold by:").
6. customer_name = the buyer/recipient ("Bill To:", "Ship To:", "Sold To:").
7. For tax fields — extract CGST, SGST, IGST separately if present.
8. line_items = array of individual products/services (can be empty array []).
9. For any field not found in the text: use null.
10. Never fabricate, guess, or hallucinate data.

## JSON SCHEMA — return exactly this structure:
{
  "invoice_number":      "string or null",
  "invoice_date":        "YYYY-MM-DD or null",
  "vendor_name":         "string or null",
  "customer_name":       "string or null",
  "total_amount":        "string or null",
  "line_items": [
    {
      "description":   "string or null",
      "hsn_sac_code":  "string or null",
      "quantity":      "string or null",
      "unit":          "string or null",
      "unit_price":    "string or null",
      "discount":      "string or null",
      "amount":        "string or null"
    }
  ],
  "due_date":            "YYYY-MM-DD or null",
  "delivery_date":       "YYYY-MM-DD or null",
  "vendor_address":      "string or null",
  "vendor_gstin":        "string or null",
  "vendor_pan":          "string or null",
  "vendor_email":        "string or null",
  "vendor_phone":        "string or null",
  "vendor_bank_details": "string or null",
  "customer_address":    "string or null",
  "customer_gstin":      "string or null",
  "customer_contact":    "string or null",
  "subtotal":            "string or null",
  "discount_overall":    "string or null",
  "shipping_charges":    "string or null",
  "cgst":                "string or null",
  "sgst":                "string or null",
  "igst":                "string or null",
  "round_off":           "string or null",
  "currency":            "3-letter code or null",
  "payment_method":      "string or null",
  "transaction_id":      "string or null",
  "payment_date":        "YYYY-MM-DD or null",
  "payment_status":      "string or null",
  "place_of_supply":     "string or null",
  "reverse_charge":      "Yes / No / null",
  "notes":               "string or null"
}"""

USER_PROMPT = """Extract all invoice details from the text below. Return ONLY the JSON object.

Invoice Text:
{text}"""


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _safe_str(v) -> Optional_str:
    """Convert any value to str or None."""
    if v is None or v == "" or str(v).lower() in ("null", "none", "n/a", "na", "-"):
        return None
    return str(v).strip()


def _parse_line_items(raw_items) -> list:
    if not isinstance(raw_items, list):
        return []
    result = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        safe = {k: _safe_str(item.get(k)) for k in
                ["description","hsn_sac_code","quantity","unit","unit_price","discount","amount"]}
        result.append(LineItem(**safe))
    return result


def extract_invoice_data(
    text: str,
    api_key: str,
    model: str = "llama-3.3-70b-versatile",
) -> InvoiceData:
    """Call Groq, parse response, return validated InvoiceData. Never raises validation errors."""
    if not text.strip():
        return InvoiceData()

    if len(text) > 14000:
        text = text[:14000] + "\n...[truncated]"

    llm = ChatGroq(
        api_key=api_key,
        model=model,
        temperature=0.0,
        max_tokens=2048,
        timeout=60,
        max_retries=2,
    )

    logger.info(f"Calling {model} with {len(text)} chars...")
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=USER_PROMPT.format(text=text)),
    ])
    raw = response.content
    logger.debug(f"LLM response (first 500): {raw[:500]}")

    # Parse JSON
    cleaned = _clean_json(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except Exception:
                logger.error("JSON parse failed completely")
                return InvoiceData()
        else:
            logger.error("No JSON found in LLM response")
            return InvoiceData()

    if not isinstance(data, dict):
        return InvoiceData()

    # Build safe scalar fields
    scalar_fields = [
        "invoice_number","invoice_date","vendor_name","customer_name","total_amount",
        "due_date","delivery_date","vendor_address","vendor_gstin","vendor_pan",
        "vendor_email","vendor_phone","vendor_bank_details","customer_address",
        "customer_gstin","customer_contact","subtotal","discount_overall",
        "shipping_charges","cgst","sgst","igst","round_off","currency",
        "payment_method","transaction_id","payment_date","payment_status",
        "place_of_supply","reverse_charge","notes",
    ]
    safe = {f: _safe_str(data.get(f)) for f in scalar_fields}
    safe["line_items"] = _parse_line_items(data.get("line_items", []))

    return InvoiceData(**safe)


