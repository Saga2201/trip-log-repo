@echo off
setlocal
cd /d "%~dp0"

:: ── Guard: ensure setup has been run ─────────────────────────
IF NOT EXIST ".venv\Scripts\python.exe" (
    echo.
    echo  ERROR: .venv not found.
    echo  Please run setup.bat first to install all dependencies.
    echo.
    pause
    exit /b 1
)

echo.
echo  ==========================================
echo    TripLog ^|  Starting Application
echo  ==========================================
echo.

:: ── Start FastAPI backend ─────────────────────────────────────
echo  Starting backend   (FastAPI  ^|  http://localhost:8001) ...
start "TripLog - Backend"  cmd /k ".venv\Scripts\python backend\run.py"

:: ── Start React / Vite frontend ───────────────────────────────
echo  Starting frontend  (React    ^|  http://localhost:5173) ...
start "TripLog - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo  ==========================================
echo    TripLog is booting up...
echo  ==========================================
echo.
echo    Backend API  :  http://localhost:8001
echo    Frontend UI  :  http://localhost:5173
echo.
echo  Opening browser in 3 seconds...
echo  Tip: close the Backend / Frontend windows to stop the servers.
echo.
timeout /t 3 /nobreak >nul
start http://localhost:5173

endlocal