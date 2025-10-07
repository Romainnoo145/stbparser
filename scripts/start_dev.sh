#!/bin/bash
# Start development environment

set -e

echo "🚀 Starting Offorte-Airtable Sync Agent (Development Mode)"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Run ./scripts/setup.sh first"
    exit 1
fi

# Check Redis
echo "Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi
echo "✅ Redis is running"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo ""
echo "Starting services in separate terminals..."
echo ""
echo "📡 FastAPI Server (port 8000)"
echo "   Command: uvicorn backend.api.server:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🔄 Celery Worker"
echo "   Command: celery -A backend.workers.worker worker --loglevel=info"
echo ""
echo "You need to run these commands in separate terminals:"
echo ""
echo "Terminal 1:"
echo "  source venv/bin/activate"
echo "  uvicorn backend.api.server:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Terminal 2:"
echo "  source venv/bin/activate"
echo "  celery -A backend.workers.worker worker --loglevel=info"
echo ""
echo "Or use tmux/screen to run them in the background"
