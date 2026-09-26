#!/usr/bin/env bash
#
# start.sh — one-command setup + launch for JB Transports (macOS / Linux)
#
# Usage:   ./start.sh
#
# What it does (idempotent — safe to re-run any time):
#   1. Verifies python3 and node/npm are installed
#   2. On macOS: installs WeasyPrint's system libs via Homebrew if missing
#   3. Creates .venv (if not present) and installs backend Python deps
#   4. Installs frontend npm deps (if node_modules missing)
#   5. Initializes the SQLite database (if not present)
#   6. Starts the FastAPI backend on http://127.0.0.1:8001
#   7. Starts the React/Vite frontend on http://localhost:5173
#   8. Opens the app in your default browser
#
# Press Ctrl+C in this terminal to stop both servers cleanly.
#
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}[start.sh]${NC} $1"; }
ok()   { echo -e "${GREEN}   ✓${NC} $1"; }
warn() { echo -e "${YELLOW}   !${NC} $1"; }
err()  { echo -e "${RED}   ✗${NC} $1" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  JB Transports — one-command startup${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"

# ── Detect OS ────────────────────────────────────────────
OS="unknown"
case "$(uname -s)" in
    Darwin*) OS="macos" ;;
    Linux*)  OS="linux" ;;
esac
log "OS detected: $OS"

# ── 1. Python 3 ──────────────────────────────────────────
log "[1/7] Checking python3..."
if ! command -v python3 &> /dev/null; then
    err "python3 not found on PATH."
    if [ "$OS" = "macos" ]; then
        err "Install with:  brew install python@3.11"
        err "Or download:   https://www.python.org/downloads/"
    else
        err "Install with:  sudo apt install python3 python3-venv python3-pip"
    fi
    exit 1
fi
ok "$(python3 --version)"

# ── 2. Node.js + npm ─────────────────────────────────────
log "[2/7] Checking node + npm..."
if ! command -v node &> /dev/null; then
    err "node not found on PATH."
    if [ "$OS" = "macos" ]; then
        err "Install with:  brew install node"
    else
        err "Install from:  https://nodejs.org/"
    fi
    exit 1
fi
if ! command -v npm &> /dev/null; then
    err "npm not found. Reinstall Node.js from https://nodejs.org/"
    exit 1
fi
ok "node $(node --version), npm $(npm --version)"

# ── 3. macOS WeasyPrint system deps ──────────────────────
if [ "$OS" = "macos" ]; then
    log "[3/7] Checking WeasyPrint system libraries (Homebrew)..."
    if command -v brew &> /dev/null; then
        MISSING=()
        for pkg in pango gdk-pixbuf libffi; do
            brew list "$pkg" &>/dev/null || MISSING+=("$pkg")
        done
        if [ ${#MISSING[@]} -gt 0 ]; then
            log "Installing missing WeasyPrint deps: ${MISSING[*]}"
            brew install "${MISSING[@]}"
        fi
        ok "WeasyPrint system libs present (pango, gdk-pixbuf, libffi)"
    else
        warn "Homebrew not found — PDF generation may fail."
        warn "Install brew from https://brew.sh/ if PDFs error out."
    fi
else
    log "[3/7] Skipping macOS-specific WeasyPrint deps"
fi

# ── 4. Python venv + backend deps ────────────────────────
log "[4/7] Setting up Python virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    ok ".venv created"
else
    ok ".venv already exists"
fi
# shellcheck disable=SC1091
source .venv/bin/activate

log "         Installing backend Python packages (quiet)..."
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r backend/requirements.txt
ok "backend deps ready"

# ── 5. Frontend deps ─────────────────────────────────────
log "[5/7] Installing frontend npm packages..."
if [ ! -d "frontend/node_modules" ]; then
    log "         First-time install — this may take a minute..."
    (cd frontend && npm install --silent)
    ok "frontend deps installed"
else
    ok "frontend/node_modules present (skipped — delete it to force reinstall)"
fi

# ── 6. Initialize database (idempotent) ──────────────────
log "[6/7] Initializing database..."
python3 -c "import database; database.init_db()"
ok "trips.db ready"

# ── 7. Start servers ─────────────────────────────────────
log "[7/7] Starting servers..."

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo
    log "Shutting down..."
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    # Also kill any lingering vite / uvicorn subprocesses
    pkill -f "vite" 2>/dev/null || true
    pkill -f "uvicorn.*api:app" 2>/dev/null || true
    sleep 0.5
    ok "Stopped. Goodbye!"
    exit 0
}
trap cleanup INT TERM

# Free the ports first if something's holding them
for PORT in 8001 5173; do
    PID=$(lsof -ti :$PORT 2>/dev/null || true)
    if [ -n "$PID" ]; then
        warn "Port $PORT was in use by pid $PID — killing it"
        kill "$PID" 2>/dev/null || true
        sleep 0.5
    fi
done

# Backend
log "         Backend  → http://127.0.0.1:8001"
(cd backend && python3 run.py) > /tmp/jb-backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to bind port 8001 (up to 15s)
for i in {1..30}; do
    if lsof -ti :8001 &>/dev/null; then
        ok "backend ready (pid $BACKEND_PID)"
        break
    fi
    sleep 0.5
done
if ! lsof -ti :8001 &>/dev/null; then
    err "Backend failed to start. See /tmp/jb-backend.log for details:"
    tail -20 /tmp/jb-backend.log
    cleanup
    exit 1
fi

# Frontend
log "         Frontend → http://localhost:5173"
(cd frontend && npm run dev) > /tmp/jb-frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for vite to bind port 5173 (up to 30s — first build is slower)
for i in {1..60}; do
    if lsof -ti :5173 &>/dev/null; then
        ok "frontend ready (pid $FRONTEND_PID)"
        break
    fi
    sleep 0.5
done
if ! lsof -ti :5173 &>/dev/null; then
    err "Frontend failed to start. See /tmp/jb-frontend.log for details:"
    tail -20 /tmp/jb-frontend.log
    cleanup
    exit 1
fi

# Open browser
sleep 1
if [ "$OS" = "macos" ]; then
    open http://localhost:5173 || true
elif [ "$OS" = "linux" ] && command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173 || true
fi

echo
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ JB Transports is running${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "   App :   ${BLUE}http://localhost:5173${NC}"
echo -e "   API :   ${BLUE}http://127.0.0.1:8001${NC}"
echo -e "   Logs:   /tmp/jb-backend.log  and  /tmp/jb-frontend.log"
echo
echo -e "   Press ${YELLOW}Ctrl+C${NC} to stop both servers."
echo

# Wait indefinitely (until Ctrl+C fires cleanup)
wait
