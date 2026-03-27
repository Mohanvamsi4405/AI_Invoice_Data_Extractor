@echo off
echo ========================================
echo  AI Invoice Reader — Virtual Env Setup
echo ========================================
echo.

:: Create virtual environment
echo [1/4] Creating virtual environment...
python -m venv .venv

:: Activate
echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Upgrade pip
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo [4/4] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt

echo.
echo ========================================
echo  Setup complete!
echo ========================================
echo.
echo Next steps:
echo   1. Copy .env.example to .env
echo   2. Add your GROQ_API_KEY to .env
echo   3. Run: .venv\Scripts\activate ^& python app.py
echo   4. Open http://localhost:8000
echo.
pause
