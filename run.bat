@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ==========================================================================
::  run.bat — one-command setup + launch for JB Transports (Windows)
::
::  Usage: double-click, or run from any terminal:  run.bat
::
::  Does everything setup.bat + start.bat did, in one go:
::    1. Checks python and node/npm
::    2. Creates .venv and installs backend deps (skips if already done)
::    3. Installs frontend deps (skips if already done)
::    4. Initializes the database (idempotent)
::    5. Starts backend and frontend in their own windows
::    6. Opens the app in your browser
::  Close the "Backend" / "Frontend" console windows to stop the servers.
:: ==========================================================================

echo.
echo  ==========================================
echo    JB Transports  ^|  one-command startup
echo  ==========================================
echo.

:: ── 1. Python ────────────────────────────────────────────
echo  [1/6] Checking Python...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Python not found on PATH.
    echo  Download Python 3.9+ from https://www.python.org/downloads/
    echo  IMPORTANT: check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
FOR /f "tokens=*" %%v IN ('python --version 2^>^&1') DO echo         %%v found.

:: ── 2. Node.js / npm ─────────────────────────────────────
echo  [2/6] Checking Node.js and npm...
node --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Node.js not found on PATH.
    echo  Download Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
npm --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: npm not found. Reinstall Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
FOR /f "tokens=*" %%v IN ('node --version') DO echo         Node %%v found.
FOR /f "tokens=*" %%v IN ('npm --version') DO echo         npm  %%v found.

:: ── 3. Python venv + backend deps ────────────────────────
echo  [3/6] Setting up Python virtual environment...
IF EXIST ".venv\Scripts\python.exe" (
    echo         .venv already exists -- skipping creation.
) ELSE (
    python -m venv .venv
    IF ERRORLEVEL 1 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo         .venv created.
)

echo         Installing backend Python packages...
".venv\Scripts\python" -m pip install --quiet --upgrade pip
".venv\Scripts\pip" install --quiet -r backend\requirements.txt
IF ERRORLEVEL 1 (
    echo  ERROR: pip install failed.
    pause
    exit /b 1
)
echo         Backend deps ready.

:: ── 4. Frontend deps ─────────────────────────────────────
echo  [4/6] Installing frontend npm packages...
IF EXIST "frontend\node_modules\" (
    echo         frontend\node_modules present -- skipping. Delete it to force reinstall.
) ELSE (
    echo         First-time install -- this may take a minute...
    pushd frontend
    call npm install --silent
    IF ERRORLEVEL 1 (
        echo  ERROR: npm install failed.
        popd
        pause
        exit /b 1
    )
    popd
    echo         Frontend deps installed.
)

:: ── 5. Init database (idempotent) ────────────────────────
echo  [5/6] Initializing database...
".venv\Scripts\python" -c "import database; database.init_db()"
IF ERRORLEVEL 1 (
    echo  ERROR: Database initialization failed.
    pause
    exit /b 1
)
echo         trips.db ready.

:: ── 6. Start servers in separate windows ─────────────────
echo  [6/6] Starting servers...
echo         Backend  -^> http://localhost:8001
start "JB Transports - Backend"  cmd /k ".venv\Scripts\python backend\run.py"

echo         Frontend -^> http://localhost:5173
start "JB Transports - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo  ==========================================
echo    JB Transports is booting up...
echo  ==========================================
echo.
echo    Backend API :  http://localhost:8001
echo    Frontend UI :  http://localhost:5173
echo.
echo  Opening browser in 5 seconds...
echo  Tip: close the Backend / Frontend windows to stop the servers.
echo.
timeout /t 5 /nobreak >nul
start http://localhost:5173

endlocal
