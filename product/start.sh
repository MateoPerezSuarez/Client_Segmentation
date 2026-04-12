#!/usr/bin/env bash
# Starts both the FastAPI backend and the Vite frontend dev server.
# Run from the project root:  bash product/start.sh
# Or from product/:           bash start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$SCRIPT_DIR/backend"
FRONTEND="$SCRIPT_DIR/frontend"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Customer Segmentation – Dev Start  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"

# ── Resolve Python / pip / uvicorn commands (Windows uses 'py' or 'python3') ──
PYTHON=""
for cmd in python3 python py; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON="$cmd"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo -e "${RED}✗ Python not found. Install Python 3 and make sure it is on your PATH.${NC}"
  exit 1
fi
echo -e "  Using Python: $PYTHON ($($PYTHON --version))"

PIP=""
for cmd in pip3 pip "py -m pip"; do
  if command -v "$cmd" >/dev/null 2>&1 || $PYTHON -m pip --version >/dev/null 2>&1; then
    PIP="$PYTHON -m pip"
    break
  fi
done

UVICORN="$PYTHON -m uvicorn"

# ── Ensure Node.js is on PATH (Windows installs it outside Git Bash's PATH) ───
NODE_CANDIDATES=(
  "/c/Program Files/nodejs"
  "/c/Program Files (x86)/nodejs"
  "$HOME/AppData/Roaming/nvm/current"
  "$HOME/scoop/shims"
)
if ! command -v node >/dev/null 2>&1; then
  for dir in "${NODE_CANDIDATES[@]}"; do
    if [ -f "$dir/node.exe" ] || [ -f "$dir/node" ]; then
      export PATH="$dir:$PATH"
      echo -e "  Added Node.js to PATH from: $dir"
      break
    fi
  done
fi

for cmd in node npm; do
  command -v "$cmd" >/dev/null 2>&1 || { echo -e "${RED}✗ '$cmd' not found. Install Node.js from https://nodejs.org${NC}"; exit 1; }
done
echo -e "  Using Node: $(node --version), npm: $(npm --version)"

# ── Backend: install deps if needed, then start ───────────────────────────────
echo -e "\n${GREEN}▶ Starting backend (FastAPI on :8000)…${NC}"

cd "$BACKEND"

echo "  Syncing Python dependencies…"
$PIP install -r requirements.txt -q

$UVICORN main:app --reload --port 8000 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# ── Frontend: install deps if needed, then start ─────────────────────────────
echo -e "\n${GREEN}▶ Starting frontend (Vite on :5173)…${NC}"

cd "$FRONTEND"

if [ ! -d "node_modules" ]; then
  echo "  Installing npm dependencies…"
  npm install -q
fi

npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

# ── Wait and handle Ctrl+C ────────────────────────────────────────────────────
echo -e "\n${CYAN}Both servers are running.${NC}"
echo -e "  Backend:  http://localhost:8000"
echo -e "  Frontend: http://localhost:5173"
echo -e "  API docs: http://localhost:8000/docs"
echo -e "\nPress ${RED}Ctrl+C${NC} to stop both servers.\n"

cleanup() {
  echo -e "\n${RED}Shutting down…${NC}"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  echo "Done."
}

trap cleanup INT TERM
wait
