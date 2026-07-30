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
if [[ "$DATABASE_URL" == postgresql* ]]; then
    if command -v psql &> /dev/null; then
        if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw nerve_health; then
            echo "[OK] PostgreSQL database 'nerve_health' exists"
        else
            echo "[WARN] PostgreSQL database 'nerve_health' not found; using SQLite instead."
            export DATABASE_URL="sqlite:///./data/healthcare.db"
        fi
    else
        echo "[WARN] psql not found; using SQLite instead."
        export DATABASE_URL="sqlite:///./data/healthcare.db"
    fi
else
    echo "[OK] Using configured database URL"
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
MIGRATION_OUT=$(DATABASE_URL="${DATABASE_URL:-sqlite:///./data/healthcare.db}" alembic upgrade head 2>&1)
MIGRATION_STATUS=$?
if [ $MIGRATION_STATUS -eq 0 ]; then
    echo "[OK] Database migrations completed"
else
    if echo "$MIGRATION_OUT" | grep -q "already exists"; then
        echo "[INFO] Database tables exist without Alembic history. Stamping to head revision..."
        if DATABASE_URL="${DATABASE_URL:-sqlite:///./data/healthcare.db}" alembic stamp head >/dev/null 2>&1; then
            echo "[OK] Database schema stamped to head revision successfully"
        else
            echo "[WARN] Could not stamp database revision"
        fi
    else
        echo "$MIGRATION_OUT"
        echo "[WARN] Migration command reported a problem; continuing with the existing database state"
    fi
fi
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

BACKEND_PID=""
FRONTEND_PID=""

if curl -sf http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    echo "[OK] Backend is already running"
    BACKEND_PID=$(lsof -ti :8000 2>/dev/null | head -n 1)
else
    echo "[START] Starting backend server..."
    cd "$SCRIPT_DIR/backend"
    source venv/bin/activate
    (uvicorn app.main:app --host localhost --port 8000 --access-log --log-level info 2>&1 | tee -a "$SCRIPT_DIR/backend/.startup_backend.log") &
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
fi

if curl -sf http://127.0.0.1:5173 >/dev/null 2>&1; then
    echo "[OK] Frontend is already running"
    FRONTEND_PID=$(lsof -ti :5173 2>/dev/null | head -n 1)
else
    echo "[START] Starting frontend development server..."
    cd "$SCRIPT_DIR/frontend"
    npm run dev -- --host :: --port 5173 --strictPort > "$SCRIPT_DIR/frontend/.startup_frontend.log" 2>&1 &
    FRONTEND_PID=$!
    cd "$SCRIPT_DIR"

    for i in $(seq 1 20); do
        if curl -sf http://127.0.0.1:5173 >/dev/null 2>&1; then
            echo "[OK] Frontend is ready"
            break
        fi
        sleep 1
    done

    if ! curl -sf http://127.0.0.1:5173 >/dev/null 2>&1; then
        echo "[WARN] Frontend health check failed; check $SCRIPT_DIR/frontend/.startup_frontend.log for details"
    fi
fi

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

cleanup() {
    echo ""
    echo "Stopping AI Healthcare Assistant..."
    pkill -f "uvicorn app.main:app" 2>/dev/null
    pkill -f "npm run dev" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    echo "All services stopped"
    exit 0
}

trap cleanup INT TERM

if [ -n "$BACKEND_PID" ] && [ -n "$FRONTEND_PID" ]; then
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
elif [ -n "$BACKEND_PID" ]; then
    wait "$BACKEND_PID" 2>/dev/null
elif [ -n "$FRONTEND_PID" ]; then
    wait "$FRONTEND_PID" 2>/dev/null
fi

while true; do
    sleep 3600 &
    wait $!
done
