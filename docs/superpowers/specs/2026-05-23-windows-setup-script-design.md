# Windows Setup Script — Design Spec

**Date:** 2026-05-23  
**Author:** Claude Code  
**Status:** Approved

---

## Overview

Two Windows batch scripts placed at the project root that allow any Windows machine to install all dependencies and launch the TripLog application with minimal manual steps.

| Script | Purpose | When to run |
|---|---|---|
| `setup.bat` | Install all Python and Node.js dependencies | Once, on first use or after cloning |
| `start.bat` | Launch FastAPI backend + React frontend | Every time to start the app |

---

## Scope

The scripts cover the **FastAPI + React stack** (the primary, modern stack):

- **Backend:** `backend/run.py` → FastAPI on port `8001`
- **Frontend:** `frontend/` → React/Vite dev server on port `5173` (proxies `/api` to port `8001`)

The NiceGUI app (`main.py`, root `requirements.txt`) is out of scope for launching, but its Python dependencies are installed because both apps share the same `.venv`.

---

## `setup.bat` — First-Time Setup Script

### Location
`setup.bat` at project root (next to `main.py`, `requirements.txt`)

### Behaviour

1. **Python prerequisite check**
   - Runs `python --version` and checks exit code.
   - If Python is not found: prints error message with download URL (`https://www.python.org/downloads/`) and exits with code 1.
   - Requires Python 3.9+ (matching the existing `.venv/pyvenv.cfg`).

2. **Node.js/npm prerequisite check**
   - Runs `node --version` and `npm --version` and checks exit codes.
   - If Node or npm is not found: prints error with download URL (`https://nodejs.org/`) and exits with code 1.

3. **Virtual environment creation**
   - Checks if `.venv` folder exists (`IF EXIST .venv\`).
   - If exists: skips creation with an info message ("Existing .venv found, skipping creation").
   - If not: runs `python -m venv .venv`.

4. **Python dependency installation (root)**
   - Activates `.venv` with `.venv\Scripts\activate.bat`.
   - Runs `pip install -r requirements.txt` from project root.

5. **Python dependency installation (backend)**
   - Runs `pip install -r backend\requirements.txt`.

6. **Node.js dependency installation (frontend)**
   - Changes directory to `frontend\`.
   - Runs `npm install`.
   - Returns to project root after.

7. **Success output**
   - Prints a banner confirming setup is complete.
   - Instructs user to run `start.bat` to launch the app.

### Error handling
- Each major step is followed by `IF ERRORLEVEL 1 GOTO :error` to catch failures.
- A `:error` label at the bottom prints a generic failure message and exits with code 1.
- `@echo off` at the top suppresses noisy command echoing.

---

## `start.bat` — Application Launch Script

### Location
`start.bat` at project root

### Behaviour

1. **Guard check**
   - Checks if `.venv\Scripts\python.exe` exists.
   - If not: prints "Run setup.bat first" message and exits with code 1.

2. **Start FastAPI backend**
   - Opens a new `cmd` window (via `start "TripLog - Backend" cmd /k`) running:
     ```
     .venv\Scripts\python backend\run.py
     ```
   - Window title: `TripLog - Backend`
   - Server starts on `http://localhost:8001`

3. **Start React frontend**
   - Opens a new `cmd` window running:
     ```
     cd frontend && npm run dev
     ```
   - Window title: `TripLog - Frontend`
   - Dev server starts on `http://localhost:5173`

4. **Info output (original window)**
   - Prints:
     ```
     TripLog is starting...
     Backend:  http://localhost:8001
     Frontend: http://localhost:5173
     ```

5. **Auto-open browser**
   - Waits ~3 seconds using `timeout /t 3 /nobreak`.
   - Runs `start http://localhost:5173` to open default browser.

---

## File Layout After Setup

```
triplog/
├── setup.bat           ← NEW: first-time install
├── start.bat           ← NEW: daily launcher
├── .venv/              ← created by setup.bat
├── requirements.txt    ← root Python deps (NiceGUI + shared)
├── backend/
│   ├── requirements.txt
│   └── run.py          ← FastAPI entry point
└── frontend/
    ├── node_modules/   ← created by npm install
    └── package.json
```

---

## Prerequisites (User must install manually)

| Tool | Required version | Download |
|---|---|---|
| Python | 3.9+ | https://www.python.org/downloads/ |
| Node.js + npm | 18+ | https://nodejs.org/ |

> **Note for Windows:** When installing Python, users must check **"Add Python to PATH"** in the installer. When installing Node.js, npm is bundled automatically.

---

## Out of Scope

- Installing Python or Node.js automatically (beyond printing helpful instructions)
- Production build (`npm run build`) — this is for development use
- NiceGUI app (`main.py`) launch
- Docker or container-based setup
- Linux/macOS support (`.bat` is Windows-only by design)