#!/usr/bin/env bash
set -e

echo "=================================================="
echo "      🚀 Launching MedVerify Full-Stack App       "
echo "=================================================="

# Function to kill child processes upon exit
cleanup() {
    echo ""
    echo "Shutting down MedVerify services..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Start Backend
echo "[1/2] Starting FastAPI Backend on :8000..."
cd backend
if [ -d ".venv/bin" ]; then
    source .venv/bin/activate
elif [ -d ".venv/Scripts" ]; then
    source .venv/Scripts/activate
else
    echo "Creating virtual environment..."
    python3 -m venv .venv || python -m venv .venv
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate
    pip install -r requirements.txt
fi

python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 2. Start Frontend
echo "[2/2] Starting Vite Frontend on :5173..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================================="
echo " MedVerify is LIVE!"
echo " 👉 Web UI:     http://localhost:5173"
echo " 👉 API Health: http://localhost:8000/api/health"
echo " 👉 API Docs:   http://localhost:8000/docs"
echo " Press Ctrl + C to stop all services."
echo "=================================================="

# Wait for background jobs
wait
