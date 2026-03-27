# AI Invoice Data Extractor

Extract structured invoice data from PDF/images using AI — powered by **Groq LLM + LangChain + pdfplumber + EasyOCR**.

## Features
- Upload PDF or image invoices (PNG, JPG, TIFF, etc.)
- Extracts 30+ fields: vendor, customer, line items, GSTIN, CGST/SGST/IGST, bank details, payment info, compliance fields
- Saves all data to a formatted Excel file (35 columns)
- Beautiful step-by-step UI with live progress
- REST API with FastAPI + Swagger docs at `/api/docs`

## Tech Stack
- **Backend**: FastAPI (Python 3.12)
- **LLM**: LangChain + ChatGroq (Llama 3.3 70B)
- **PDF Extraction**: pdfplumber
- **Image OCR**: EasyOCR
- **Excel**: openpyxl
- **Frontend**: HTML + CSS + Vanilla JS

## Local Setup

```bash
# 1. Clone & create venv
git clone https://github.com/Mohanvamsi4405/AI_Invoice_Data_Extractor.git
cd AI_Invoice_Data_Extractor
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env → add your GROQ_API_KEY (get free at https://console.groq.com)

# 4. Run
python app.py
# → http://localhost:8000
```

## Render Deployment
1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → Connect repo
3. Render auto-detects `render.yaml` (Docker runtime)
4. Set `GROQ_API_KEY` in Render Dashboard → Environment
5. Deploy ✅

## Environment Variables
| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Get free at console.groq.com |
| `PORT` | Auto | Set by Render (10000) |
| `ENV` | Optional | `development` enables hot-reload |
| `EXCEL_PATH` | Optional | Default: `data/invoices.xlsx` |
