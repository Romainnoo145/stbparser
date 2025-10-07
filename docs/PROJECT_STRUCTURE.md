# Project Structure Guide

## Overview

This document explains the reorganized directory structure of the Offorte-Airtable Sync Agent project.

## Directory Tree

```
offorte_airtable_sync/
│
├── backend/                         # All Python application code
│   ├── __init__.py
│   ├── agent/                       # Pydantic AI Agent
│   │   ├── __init__.py
│   │   ├── agent.py                 # Main agent with tool registration
│   │   ├── tools.py                 # 6 agent tools (547 lines)
│   │   └── prompts.py               # System prompts
│   ├── core/                        # Core Infrastructure
│   │   ├── __init__.py
│   │   ├── settings.py              # Environment configuration
│   │   ├── providers.py             # LLM model providers
│   │   └── dependencies.py          # Dependency injection
│   ├── api/                         # FastAPI Web Server
│   │   ├── __init__.py
│   │   └── server.py                # Webhook receiver
│   └── workers/                     # Background Processing
│       ├── __init__.py
│       └── worker.py                # Celery worker
│
├── tests/                           # Test Suite (115+ tests)
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/                        # Unit Tests
│   │   ├── test_settings.py         # Settings tests (18 tests)
│   │   ├── test_dependencies.py     # Dependencies tests (17 tests)
│   │   ├── test_tools.py            # Tools tests (30+ tests)
│   │   └── test_agent.py            # Agent tests (15 tests)
│   ├── integration/                 # Integration Tests
│   │   ├── test_server.py           # Server tests (20+ tests)
│   │   └── test_integration.py      # E2E tests (15+ tests)
│   └── fixtures/                    # Test Data
│       └── (test data files)
│
├── docs/                            # Documentation
│   ├── PROJECT_STRUCTURE.md         # This file
│   ├── USER_GUIDE.md                # Complete user guide
│   ├── TESTING.md                   # Test documentation
│   ├── VALIDATION_REPORT.md         # PRP validation results
│   └── TEST_SUMMARY.md              # Quick test reference
│
├── examples/                        # Usage Examples
│   └── simple_sync.py               # Basic sync example
│
├── config/                          # Configuration Files
│   └── table_mappings.yaml          # Airtable table configs
│
├── scripts/                         # Helper Scripts
│   ├── setup.sh                     # Initial setup script
│   └── start_dev.sh                 # Start development environment
│
├── planning/                        # Design Documents (from PRP)
│   ├── prompts.md                   # Prompt specifications
│   ├── tools.md                     # Tool specifications
│   └── dependencies.md              # Dependency specifications
│
├── .env.example                     # Environment variable template
├── .env                             # Your configuration (gitignored)
├── requirements.txt                 # Python dependencies
├── requirements-test.txt            # Test dependencies
├── pytest.ini                       # Pytest configuration
├── .gitignore                       # Git ignore rules
└── README.md                        # Project README
```

## Module Organization

### backend/

The `backend/` directory contains all Python application code, organized into logical modules:

#### backend/agent/
**Purpose**: Pydantic AI agent implementation

- `agent.py` - Main agent initialization, tool registration, entry point
- `tools.py` - 6 essential tools for sync pipeline
- `prompts.py` - System prompts for agent behavior

**Imports**:
```python
from backend.agent.agent import agent, process_proposal_sync
from backend.agent.tools import fetch_proposal_data, validate_webhook
from backend.agent.prompts import SYSTEM_PROMPT
```

#### backend/core/
**Purpose**: Core infrastructure and configuration

- `settings.py` - Environment variable loading with pydantic-settings
- `providers.py` - LLM model provider configuration (OpenAI)
- `dependencies.py` - Dependency injection dataclass

**Imports**:
```python
from backend.core.settings import settings, load_settings
from backend.core.providers import get_llm_model
from backend.core.dependencies import AgentDependencies
```

#### backend/api/
**Purpose**: FastAPI web server for webhooks

- `server.py` - FastAPI app, webhook endpoints, health checks

**Imports**:
```python
from backend.api.server import app
```

**Run**:
```bash
uvicorn backend.api.server:app --host 0.0.0.0 --port 8000
```

#### backend/workers/
**Purpose**: Background job processing

- `worker.py` - Celery worker configuration and tasks

**Imports**:
```python
from backend.workers.worker import celery_app, sync_proposal_task
```

**Run**:
```bash
celery -A backend.workers.worker worker --loglevel=info
```

### tests/

Test suite organized by test type:

#### tests/unit/
**Purpose**: Fast, isolated unit tests

- Test individual functions and classes
- Mock all external dependencies
- No network calls or I/O

#### tests/integration/
**Purpose**: Integration tests with multiple components

- Test component interactions
- Mock external APIs but test internal integration
- End-to-end workflow testing

#### tests/fixtures/
**Purpose**: Shared test data

- Dutch proposal examples
- Mock API responses
- Reusable test data

### docs/

All documentation in one place:

- `PROJECT_STRUCTURE.md` - This file (navigation guide)
- `USER_GUIDE.md` - Complete user documentation
- `TESTING.md` - How to run and write tests
- `VALIDATION_REPORT.md` - PRP validation results
- `TEST_SUMMARY.md` - Quick test reference

### examples/

Runnable code examples showing how to use the agent:

- `simple_sync.py` - Basic manual sync example
- (Add more examples as needed)

### config/

Configuration files for the application:

- `table_mappings.yaml` - Airtable table mapping configuration
- (Add more config files as needed)

### scripts/

Helper scripts for common tasks:

- `setup.sh` - One-command project setup
- `start_dev.sh` - Start development environment
- (Add more scripts as needed)

## Import Patterns

### From Application Code

```python
# Core infrastructure
from backend.core.settings import settings
from backend.core.providers import get_llm_model
from backend.core.dependencies import AgentDependencies

# Agent code
from backend.agent.agent import agent, process_proposal_sync
from backend.agent.tools import fetch_proposal_data
from backend.agent.prompts import SYSTEM_PROMPT

# API
from backend.api.server import app

# Workers
from backend.workers.worker import celery_app
```

### From Tests

```python
# Same imports as application code
from backend.core.settings import Settings
from backend.agent.agent import agent
```

### Running Commands

```bash
# FastAPI server
uvicorn backend.api.server:app --reload

# Celery worker
celery -A backend.workers.worker worker --loglevel=info

# Tests
pytest                          # All tests
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only

# Examples
python examples/simple_sync.py
```

## Configuration at Root

Following industry standards, configuration files are at the project root:

- `.env` - Your actual configuration (never commit!)
- `.env.example` - Template showing required variables
- `requirements.txt` - Python dependencies
- `requirements-test.txt` - Test dependencies
- `pytest.ini` - Pytest configuration
- `README.md` - Project overview

## Navigation Tips

### Finding Code

- **Agent logic** → `backend/agent/`
- **Settings & config** → `backend/core/`
- **Web server** → `backend/api/`
- **Background jobs** → `backend/workers/`

### Finding Tests

- **Unit tests** → `tests/unit/`
- **Integration tests** → `tests/integration/`
- **Test fixtures** → `tests/conftest.py` and `tests/fixtures/`

### Finding Documentation

- **User guide** → `docs/USER_GUIDE.md`
- **Test guide** → `docs/TESTING.md`
- **This navigation guide** → `docs/PROJECT_STRUCTURE.md`

### Finding Examples

- **Code examples** → `examples/`
- **Quick start** → `README.md`

## Benefits of This Structure

✅ **Clear Separation** - Backend, tests, docs all separate
✅ **Easy Navigation** - Logical grouping of related code
✅ **Industry Standard** - Config at root, tests at root
✅ **Scalable** - Easy to add new modules/features
✅ **Maintainable** - Clear responsibility for each directory
✅ **Professional** - Follows Python project best practices
✅ **Testable** - Tests organized by type (unit/integration)
✅ **Documented** - All docs in one place

## Adding New Features

### Adding a New Tool
1. Add function to `backend/agent/tools.py`
2. Register in `backend/agent/agent.py`
3. Add tests in `tests/unit/test_tools.py`
4. Update documentation

### Adding a New Table
1. Update `config/table_mappings.yaml`
2. Update transformation in `backend/agent/tools.py`
3. Add tests for new table
4. Update documentation

### Adding a New API Endpoint
1. Add route to `backend/api/server.py`
2. Add tests in `tests/integration/test_server.py`
3. Update API documentation

## Migrating from Old Structure

If you have code referencing the old structure:

**Old imports**:
```python
from offorte_airtable_sync.settings import settings
from offorte_airtable_sync.agent import agent
```

**New imports**:
```python
from backend.core.settings import settings
from backend.agent.agent import agent
```

**Old commands**:
```bash
uvicorn offorte_airtable_sync.server:app
celery -A offorte_airtable_sync.worker worker
```

**New commands**:
```bash
uvicorn backend.api.server:app
celery -A backend.workers.worker worker
```

## Questions?

- Check [README.md](../README.md) for quick start
- See [docs/USER_GUIDE.md](USER_GUIDE.md) for detailed documentation
- Review [examples/](../examples/) for code examples
