# ────────────────────────────────────────────────────────────
# AI Invoice Reader — Dockerfile
# Multi-stage build for optimized production image
# ────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# System dependencies for pdfplumber, EasyOCR, and Pillow
# libgl1 replaces libgl1-mesa-glx on Debian Trixie (13+)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    poppler-utils \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Optional: Tesseract OCR fallback
# RUN apt-get install -y tesseract-ocr

WORKDIR /app

# Install Python dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download EasyOCR English model to avoid cold-start delay
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False, verbose=False)" || true

# Copy application source
COPY . .

# Create necessary directories
RUN mkdir -p uploads data

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Render uses PORT=10000; local default is 8000
EXPOSE 10000

# Health check (uses $PORT at runtime via shell form)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen(f\"http://localhost:{os.getenv('PORT','10000')}/api/health\")" || exit 1

# Shell form so $PORT is expanded at runtime
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1
