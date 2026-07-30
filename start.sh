#!/bin/bash

echo "=========================================="
echo "  Nerve - AI Healthcare Assistant"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$SCRIPT_DIR/backend/.env" ]; then
    echo "[ERROR] .env file not found in backend/"
    echo "Please copy backend/.env.example to backend/.env and configure it"
    exit 1
fi

if grep -q "your-mistral-api-key-here" "$SCRIPT_DIR/backend/.env"; then
    echo "[ERROR] Please set your MISTRAL_API_KEY in backend/.env"
    exit 1
fi

set -a
source "$SCRIPT_DIR/backend/.env"
set +a

# ─── Database Setup ───────────────────────────────────────────────
echo "[CHECK] Database..."
if command -v psql &> /dev/null; then
    if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw nerve_health; then
        echo "[OK] PostgreSQL database 'nerve_health' exists"
    else
        echo "[WARN] PostgreSQL database 'nerve_health' not found; continuing with the local SQLite setup."
    fi
else
    echo "[WARN] psql not found; continuing with the local SQLite setup."
fi

if [ ! -d "$SCRIPT_DIR/backend/venv" ] || [ ! -f "$SCRIPT_DIR/backend/venv/bin/uvicorn" ]; then
    echo "[SETUP] Creating Python virtual environment and installing dependencies..."
    rm -rf "$SCRIPT_DIR/backend/venv"
    cd "$SCRIPT_DIR/backend"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd "$SCRIPT_DIR"
else
    echo "[OK] Python venv exists, verifying dependencies..."
    cd "$SCRIPT_DIR/backend"
    source venv/bin/activate
    pip install -q -r requirements.txt
    cd "$SCRIPT_DIR"
fi

if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "[SETUP] Installing frontend dependencies..."
    cd "$SCRIPT_DIR/frontend"
    npm install
    cd "$SCRIPT_DIR"
else
    echo "[OK] Frontend dependencies installed"
fi

mkdir -p "$SCRIPT_DIR/backend/data"

echo "[SETUP] Running database migrations..."
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
DATABASE_URL="${DATABASE_URL:-sqlite:///./data/healthcare.db}" alembic upgrade head 2>&1 || echo "[WARN] Migration failed — check DATABASE_URL in .env"
cd "$SCRIPT_DIR"

if [ ! -d "$SCRIPT_DIR/backend/data/chroma_db" ]; then
    echo "[SETUP] Ingesting medical documents..."
    cd "$SCRIPT_DIR/backend"
    source venv/bin/activate
    python ../scripts/ingest_documents.py
    cd "$SCRIPT_DIR"
else
    echo "[OK] ChromaDB has existing data"
fi

echo "[START] Starting backend server..."
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/backend/.startup_backend.log" 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

for i in $(seq 1 20); do
    if curl -sf http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
        echo "[OK] Backend is ready"
        break
    fi
    sleep 1
done

if ! curl -sf http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    echo "[WARN] Backend health check failed; check $SCRIPT_DIR/backend/.startup_backend.log for details"
fi

echo "[START] Starting frontend development server..."
cd "$SCRIPT_DIR/frontend"
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort > "$SCRIPT_DIR/frontend/.startup_frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "=========================================="
echo "  AI Healthcare Assistant v2.0 is running!"
echo "=========================================="
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "=========================================="
echo ""
echo "  Features:"
echo "  - User authentication (register/login)"
echo "  - Persistent chat history"
echo "  - Dark/Light/System theme"
echo "  - Medical knowledge RAG"
echo "  - Medication search"
echo ""
echo "Press Ctrl+C to stop both servers"

wait $BACKEND_PID $FRONTEND_PID
