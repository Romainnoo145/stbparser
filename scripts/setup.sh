#!/bin/bash
# Setup script for Offorte-Airtable Sync Agent

set -e

echo "🚀 Setting up Offorte-Airtable Sync Agent..."

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Install test dependencies
echo "Installing test dependencies..."
pip install -r requirements-test.txt
echo "✅ Test dependencies installed"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "✅ .env file created from template"
    echo ""
    echo "📝 IMPORTANT: Edit .env with your actual credentials:"
    echo "   - OFFORTE_API_KEY"
    echo "   - AIRTABLE_API_KEY"
    echo "   - LLM_API_KEY"
    echo "   - Base IDs"
    echo ""
else
    echo "✅ .env file exists"
fi

# Check Redis
echo "Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis is not running"
    echo "Start Redis with: redis-server"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your credentials"
echo "2. Start services with: ./scripts/start_dev.sh"
echo "3. Run tests with: pytest"
