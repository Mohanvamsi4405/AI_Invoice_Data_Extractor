"""
AI Invoice Reader - FastAPI Backend
Production-ready invoice extraction using pdfplumber + EasyOCR + LangChain/Groq
"""

import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from src.extractor import extract_text
from src.llm_processor import extract_invoice_data
from src.excel_handler import save_invoice_to_excel, get_all_invoices, EXCEL_PATH
from src.schemas import InvoiceResponse

# ─────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Always resolve relative to this file — works on Render, local, Docker
BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
(BASE_DIR / "data").mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
MAX_FILE_SIZE_MB = 20

# ─────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────
app = FastAPI(
    title="AI Invoice Reader",
    description="Extract invoice data from PDF/images using AI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/extract", response_model=InvoiceResponse)
async def extract_invoice(
    file: UploadFile = File(...),
    groq_api_key: Optional[str] = Form(None),
    groq_model: str = Form("llama-3.3-70b-versatile"),
):
    """
    Main endpoint: upload invoice → extract text → process with AI → save to Excel.
    """
    # Resolve API key
    api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Groq API key is required. Provide it in the form or set GROQ_API_KEY env var."
        )

    # Validate file type
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    steps = []
    temp_path = None

    try:
        # ── Step 1: Save uploaded file ──────────────────────
        steps.append("File received and validated")
        unique_name = f"{uuid.uuid4().hex}{ext}"
        temp_path = UPLOAD_DIR / unique_name

        with open(temp_path, "wb") as buffer:
            content = await file.read()

        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({size_mb:.1f} MB). Max allowed: {MAX_FILE_SIZE_MB} MB"
            )

        with open(temp_path, "wb") as buffer:
            buffer.write(content)

        logger.info(f"Saved upload: {file.filename} → {temp_path} ({size_mb:.2f} MB)")

        # ── Step 2: Extract text ────────────────────────────
        steps.append("Extracting text from document...")
        text, method, meta = extract_text(str(temp_path))

        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the document. The file may be corrupted or password-protected."
            )

        steps.append(f"Text extracted using {method} ({len(text)} characters)")
        logger.info(f"Extracted {len(text)} chars via {method}")

        # ── Step 3: Process with LLM ────────────────────────
        steps.append("Sending to AI for structured extraction...")
        invoice_data = extract_invoice_data(text, api_key, groq_model)
        steps.append(f"AI extracted: vendor='{invoice_data.vendor_name}', amount={invoice_data.total_amount}, date={invoice_data.invoice_date}")

        # ── Step 4: Save to Excel ───────────────────────────
        steps.append("Saving to Excel spreadsheet...")
        saved_to_excel = False
        excel_row = None
        excel_warning = None

        try:
            excel_row = save_invoice_to_excel(invoice_data, file.filename)
            saved_to_excel = True
            steps.append(f"Saved to Excel row #{excel_row}")
        except PermissionError as pe:
            excel_warning = str(pe)
            steps.append(f"⚠️ Excel locked — {excel_warning}")
            logger.warning(f"Excel permission error: {pe}")

        return InvoiceResponse(
            success=True,
            filename=file.filename,
            extracted_text_length=len(text),
            invoice_data=invoice_data,
            processing_steps=steps,
            saved_to_excel=saved_to_excel,
            excel_row=excel_row,
            error=excel_warning,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing {file.filename}")
        steps.append(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_path and temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.get("/api/invoices")
async def list_invoices():
    """Return all saved invoices from Excel."""
    records = get_all_invoices()
    return {"total": len(records), "invoices": records}


@app.get("/api/invoices/download")
async def download_excel():
    """Download the Excel file."""
    if not Path(EXCEL_PATH).exists():
        raise HTTPException(status_code=404, detail="No invoice data found yet.")
    return FileResponse(
        path=EXCEL_PATH,
        filename="invoices.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "production") == "development",
        log_level="info",
    )
