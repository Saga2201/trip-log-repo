@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  ==========================================
echo    TripLog ^|  Windows Setup
echo  ==========================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────
echo  [1/5] Checking Python...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Python not found on PATH.
    echo  Download Python 3.9+ from: https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
FOR /f "tokens=*" %%v IN ('python --version 2^>^&1') DO echo         %%v found.

:: ── 2. Check Node.js / npm ───────────────────────────────────
echo  [2/5] Checking Node.js ^& npm...
node --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Node.js not found on PATH.
    echo  Download Node.js 18+ from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
npm --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: npm not found. Please reinstall Node.js from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
FOR /f "tokens=*" %%v IN ('node --version') DO echo         Node %%v found.
FOR /f "tokens=*" %%v IN ('npm --version') DO echo         npm  %%v found.

:: ── 3. Create virtual environment ────────────────────────────
echo  [3/5] Setting up Python virtual environment...
IF EXIST ".venv\" (
    echo         .venv already exists -- skipping creation.
) ELSE (
    python -m venv .venv
    IF ERRORLEVEL 1 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo         .venv created successfully.
)

:: ── 4. Install Python dependencies ───────────────────────────
echo  [4/5] Installing Python dependencies...
echo         (root requirements.txt -- NiceGUI + shared)
call .venv\Scripts\activate.bat
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Failed to install requirements.txt
    pause
    exit /b 1
)
echo         (backend requirements.txt -- FastAPI + uvicorn)
pip install -r backend\requirements.txt
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Failed to install backend\requirements.txt
    pause
    exit /b 1
)

:: ── 5. Install Node.js dependencies ──────────────────────────
echo  [5/5] Installing frontend dependencies (npm install)...
cd frontend
npm install
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: npm install failed in frontend\.
    cd /d "%~dp0"
    pause
    exit /b 1
)
cd /d "%~dp0"

echo.
echo  ==========================================
echo    Setup complete!  All deps installed.
echo  ==========================================
echo.
echo  Next step: double-click  start.bat  to launch TripLog.
echo.
pause
endlocal