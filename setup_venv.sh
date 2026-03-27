#!/bin/bash
set -e

echo "========================================"
echo " AI Invoice Reader — Virtual Env Setup"
echo "========================================"
echo

# Create virtual environment
echo "[1/4] Creating virtual environment..."
python3 -m venv .venv

# Activate
echo "[2/4] Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "[3/4] Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "[4/4] Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

echo
echo "========================================"
echo " Setup complete!"
echo "========================================"
echo
echo "Next steps:"
echo "  1. cp .env.example .env"
echo "  2. Edit .env and add your GROQ_API_KEY"
echo "  3. source .venv/bin/activate && python app.py"
echo "  4. Open http://localhost:8000"
echo
