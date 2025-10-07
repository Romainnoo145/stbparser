#!/bin/bash
# Verify the new project structure

echo "🔍 Verifying Offorte-Airtable Sync Agent structure..."
echo ""

errors=0

# Check directories
echo "Checking directories..."
dirs=(
    "backend"
    "backend/agent"
    "backend/core"
    "backend/api"
    "backend/workers"
    "tests"
    "tests/unit"
    "tests/integration"
    "tests/fixtures"
    "docs"
    "examples"
    "config"
    "scripts"
)

for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir"
    else
        echo "❌ $dir (missing)"
        ((errors++))
    fi
done

echo ""
echo "Checking key files..."
files=(
    "backend/agent/agent.py"
    "backend/agent/tools.py"
    "backend/agent/prompts.py"
    "backend/core/settings.py"
    "backend/core/providers.py"
    "backend/core/dependencies.py"
    "backend/api/server.py"
    "backend/workers/worker.py"
    "tests/conftest.py"
    "tests/unit/test_settings.py"
    "tests/integration/test_server.py"
    "docs/USER_GUIDE.md"
    "docs/PROJECT_STRUCTURE.md"
    "examples/simple_sync.py"
    "config/table_mappings.yaml"
    ".env.example"
    "requirements.txt"
    "README.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        ((errors++))
    fi
done

echo ""
if [ $errors -eq 0 ]; then
    echo "✅ All checks passed! Structure is correct."
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.example to .env and configure"
    echo "2. Run: ./scripts/setup.sh"
    echo "3. Start services: ./scripts/start_dev.sh"
else
    echo "❌ Found $errors errors in structure"
    exit 1
fi
