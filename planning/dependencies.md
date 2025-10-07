# Offorte-to-Airtable Sync Agent - Dependencies Specification

## Overview

This document specifies the MINIMAL dependency and configuration requirements for the Offorte-to-Airtable sync agent. The agent is a webhook-based integration that syncs accepted proposals from Offorte to multiple Airtable bases.

**Philosophy**: Keep it simple. One LLM provider, essential environment variables only, basic dataclass dependencies.

---

## Directory Structure

```
offorte_airtable_sync/
├── __init__.py
├── settings.py          # Environment configuration with pydantic-settings
├── providers.py         # Single LLM provider configuration (OpenAI)
├── dependencies.py      # Simple dataclass for agent dependencies
├── agent.py            # Agent initialization (minimal setup)
├── server.py           # FastAPI webhook server
├── worker.py           # Background job processor
├── .env.example        # Environment variable template
└── requirements.txt    # Python dependencies
```

---

## Core Environment Variables

### Essential Configuration (.env)

```bash
# ============================================
# OFFORTE API CONFIGURATION (REQUIRED)
# ============================================
OFFORTE_API_KEY=your_offorte_api_key_here
OFFORTE_ACCOUNT_NAME=your_account_name
OFFORTE_BASE_URL=https://connect.offorte.com/api/v2

# ============================================
# AIRTABLE API CONFIGURATION (REQUIRED)
# ============================================
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ADMINISTRATION=appXXXXXXXXXXXXX
AIRTABLE_BASE_SALES_REVIEW=appYYYYYYYYYYYYY
AIRTABLE_BASE_TECHNISCH=appZZZZZZZZZZZZZ

# ============================================
# LLM CONFIGURATION (REQUIRED)
# ============================================
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o
LLM_BASE_URL=https://api.openai.com/v1

# ============================================
# SERVER CONFIGURATION (REQUIRED)
# ============================================
WEBHOOK_SECRET=generate_random_secret_for_signature_validation
SERVER_PORT=8000
SERVER_HOST=0.0.0.0

# ============================================
# REDIS CONFIGURATION (REQUIRED)
# ============================================
REDIS_URL=redis://localhost:6379/0

# ============================================
# APPLICATION SETTINGS
# ============================================
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# Rate Limiting
OFFORTE_RATE_LIMIT=30  # requests per minute
AIRTABLE_RATE_LIMIT=5  # requests per second
```

---

## Python Dependencies

### requirements.txt

```txt
# ============================================
# Core Framework
# ============================================
fastapi==0.109.0
uvicorn[standard]==0.27.0

# ============================================
# AI Agent
# ============================================
pydantic-ai>=0.1.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# ============================================
# LLM Provider
# ============================================
openai>=1.0.0

# ============================================
# API Integrations
# ============================================
httpx>=0.26.0        # Async HTTP client
pyairtable==2.2.0    # Airtable Python SDK

# ============================================
# Background Processing
# ============================================
redis>=5.0.1
celery>=5.3.0

# ============================================
# Configuration
# ============================================
python-dotenv>=1.0.0
pyyaml>=6.0.1

# ============================================
# Async Utilities
# ============================================
aiofiles>=23.0.0

# ============================================
# Development & Testing
# ============================================
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
black>=23.0.0
ruff>=0.1.0
```

---

## Configuration Files Specification

### 1. settings.py - Environment Configuration

**Purpose**: Load and validate environment variables using pydantic-settings.

**Key Requirements**:
- Use `pydantic_settings.BaseSettings`
- Load from `.env` file using `python-dotenv`
- Validate all required API keys
- Support multiple Airtable bases
- Include rate limiting configuration

**Configuration Groups**:
```python
class Settings(BaseSettings):
    # Offorte Configuration
    offorte_api_key: str
    offorte_account_name: str
    offorte_base_url: str = "https://connect.offorte.com/api/v2"
    offorte_rate_limit: int = 30  # per minute

    # Airtable Configuration
    airtable_api_key: str
    airtable_base_administration: str
    airtable_base_sales_review: str
    airtable_base_technisch: str
    airtable_rate_limit: int = 5  # per second

    # LLM Configuration
    llm_provider: str = "openai"
    llm_api_key: str
    llm_model: str = "gpt-4o"
    llm_base_url: str = "https://api.openai.com/v1"

    # Server Configuration
    webhook_secret: str
    server_port: int = 8000
    server_host: str = "0.0.0.0"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"

    # Application Settings
    app_env: str = "development"
    log_level: str = "INFO"
    debug: bool = False
    max_retries: int = 3
    timeout_seconds: int = 30
```

**Validation Rules**:
- All API keys must not be empty
- Environment must be one of: development, staging, production
- Port must be valid (1-65535)
- Redis URL must be valid format

---

### 2. providers.py - LLM Provider Configuration

**Purpose**: Simple OpenAI model provider setup.

**Pattern** (following main_agent_reference):
```python
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from .settings import settings

def get_llm_model() -> OpenAIModel:
    """Get configured OpenAI model."""
    provider = OpenAIProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key
    )
    return OpenAIModel(settings.llm_model, provider=provider)
```

**No Fallback Models**: Keep it simple - single provider only.

---

### 3. dependencies.py - Agent Dependencies

**Purpose**: Simple dataclass for dependency injection into agent runtime.

**Pattern**:
```python
from dataclasses import dataclass, field
from typing import Optional
import httpx

@dataclass
class AgentDependencies:
    """
    Minimal dependencies for sync agent.
    Injected into RunContext for tool access.
    """

    # API Keys (from settings)
    offorte_api_key: str
    airtable_api_key: str
    webhook_secret: str

    # Base IDs
    airtable_base_admin: str
    airtable_base_sales: str
    airtable_base_tech: str

    # Configuration
    max_retries: int = 3
    timeout: int = 30

    # Session Context
    job_id: Optional[str] = None
    proposal_id: Optional[int] = None

    # HTTP Client (lazy init)
    _http_client: Optional[httpx.AsyncClient] = field(
        default=None,
        init=False,
        repr=False
    )

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=100)
            )
        return self._http_client

    async def cleanup(self):
        """Cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()

    @classmethod
    def from_settings(cls, settings, **overrides):
        """Create from settings with optional overrides."""
        return cls(
            offorte_api_key=settings.offorte_api_key,
            airtable_api_key=settings.airtable_api_key,
            webhook_secret=settings.webhook_secret,
            airtable_base_admin=settings.airtable_base_administration,
            airtable_base_sales=settings.airtable_base_sales_review,
            airtable_base_tech=settings.airtable_base_technisch,
            max_retries=settings.max_retries,
            timeout=settings.timeout_seconds,
            **overrides
        )
```

**Key Features**:
- Simple dataclass (no complex classes)
- Lazy HTTP client initialization
- Cleanup method for resources
- Factory method from settings
- Session-specific context (job_id, proposal_id)

---

### 4. agent.py - Agent Initialization

**Purpose**: Minimal agent setup with dependencies.

**Pattern**:
```python
from pydantic_ai import Agent
from .providers import get_llm_model
from .dependencies import AgentDependencies
from .settings import settings

# System prompt will be provided by prompt-engineer
SYSTEM_PROMPT = """
[Prompt will be inserted by prompt-engineer subagent]
"""

# Initialize agent
agent = Agent(
    get_llm_model(),
    deps_type=AgentDependencies,
    system_prompt=SYSTEM_PROMPT,
    retries=settings.max_retries
)

# Tools will be registered by tool-integrator
# from .tools import register_tools
# register_tools(agent)

async def process_proposal_sync(
    proposal_id: int,
    job_id: str
) -> dict:
    """
    Main entry point for proposal sync.

    Args:
        proposal_id: Offorte proposal ID
        job_id: Background job identifier

    Returns:
        Sync status report
    """
    deps = AgentDependencies.from_settings(
        settings,
        proposal_id=proposal_id,
        job_id=job_id
    )

    try:
        result = await agent.run(
            f"Sync proposal {proposal_id} to Airtable",
            deps=deps
        )
        return result.data
    finally:
        await deps.cleanup()
```

---

### 5. server.py - FastAPI Webhook Server

**Purpose**: Receive webhooks and queue for processing.

**Key Requirements**:
- Response time < 5 seconds (critical!)
- Validate webhook signatures
- Queue jobs to Redis immediately
- Return 200 OK before processing

**Minimal Structure**:
```python
from fastapi import FastAPI, Request, HTTPException
from .settings import settings
import redis.asyncio as redis

app = FastAPI(title="Offorte-Airtable Sync")
redis_client = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = await redis.from_url(settings.redis_url)

@app.post("/webhook/offorte")
async def receive_webhook(request: Request):
    """
    Receive Offorte webhook - MUST respond < 5 seconds.
    """
    payload = await request.json()
    signature = request.headers.get("X-Offorte-Signature")

    # Validate signature
    # ... validation logic ...

    if payload["type"] == "proposal_won":
        # Queue for background processing
        await redis_client.rpush("sync_queue", json.dumps({
            "proposal_id": payload["data"]["id"],
            "event": "proposal_won",
            "timestamp": datetime.now().isoformat()
        }))

    return {"status": "accepted"}
```

---

### 6. worker.py - Background Job Processor

**Purpose**: Process queued sync jobs using Celery.

**Key Requirements**:
- Poll Redis queue
- Call agent for each job
- Implement retry logic
- Log all operations

**Minimal Structure**:
```python
from celery import Celery
from .agent import process_proposal_sync
from .settings import settings

celery_app = Celery(
    "offorte_sync_worker",
    broker=settings.redis_url,
    backend=settings.redis_url
)

@celery_app.task(bind=True, max_retries=3)
async def sync_proposal_task(self, proposal_id: int):
    """
    Background task to sync proposal.
    """
    try:
        result = await process_proposal_sync(
            proposal_id=proposal_id,
            job_id=self.request.id
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

---

## External Service Configuration

### Offorte API Client

**Base Configuration**:
```python
class OfforteClient:
    def __init__(self, api_key: str, account_name: str):
        self.base_url = f"https://connect.offorte.com/api/v2/{account_name}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.rate_limiter = RateLimiter(30, 60)  # 30 req/min
```

**Endpoints Used**:
- GET `/proposals/{id}` - Fetch proposal details
- GET `/proposals/{id}/content` - Get line items and elements
- GET `/companies/{id}` - Customer information
- GET `/contacts/{id}` - Contact details

### Airtable API Client

**Base Configuration**:
```python
from pyairtable import Api

class AirtableClient:
    def __init__(self, api_key: str):
        self.api = Api(api_key)
        self.rate_limiter = RateLimiter(5, 1)  # 5 req/sec

    def get_table(self, base_id: str, table_name: str):
        return self.api.table(base_id, table_name)
```

**Tables Used**:
- `klantenportaal` (Customer Portal) - Base: Administration
- `facturatie` (Invoicing) - Base: Administration
- `inmeetplanning` (Measurement Planning) - Base: Technical
- `elementen_review` (Elements) - Base: Sales Review
- `projecten` (Projects) - Base: Administration
- `deur_specificaties` (Door Specs) - Base: Technical

### Redis Queue Client

**Configuration**:
```python
import redis.asyncio as redis

async def create_redis_client(redis_url: str):
    return await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )
```

---

## Rate Limiting Strategy

### Offorte Rate Limits
- **Limit**: 30 requests per minute
- **Strategy**: Token bucket algorithm
- **Implementation**: Use `aiolimiter` package

### Airtable Rate Limits
- **Limit**: 5 requests per second
- **Strategy**: Batch operations (max 10 records per request)
- **Implementation**: Combine multiple records into single API call

---

## Security Considerations

### API Key Management
- Store all keys in `.env` file
- Never commit `.env` to version control
- Use `.env.example` as template
- Validate keys on startup

### Webhook Security
- Validate webhook signatures using HMAC
- Use `webhook_secret` from environment
- Reject requests without valid signature
- Log all validation failures

### Data Sanitization
- Validate all Offorte data before Airtable writes
- Sanitize HTML/special characters in text fields
- Validate Dutch number formats (€ 1.234,56)
- Check field lengths against Airtable limits

---

## Testing Configuration

### Test Dependencies

```python
# conftest.py
import pytest
from pydantic_ai.models.test import TestModel

@pytest.fixture
def test_settings():
    """Mock settings for testing."""
    return Settings(
        offorte_api_key="test-offorte-key",
        airtable_api_key="test-airtable-key",
        llm_api_key="test-llm-key",
        webhook_secret="test-secret",
        redis_url="redis://localhost:6379/1",  # Test DB
        debug=True
    )

@pytest.fixture
def test_dependencies(test_settings):
    """Test dependencies."""
    return AgentDependencies.from_settings(
        test_settings,
        job_id="test-job-123"
    )

@pytest.fixture
def test_agent():
    """Agent with TestModel."""
    from pydantic_ai import Agent
    return Agent(
        TestModel(),
        deps_type=AgentDependencies
    )
```

---

## Monitoring & Observability

### Logging Configuration
```python
import logging
from loguru import logger

# Configure structured logging
logger.add(
    "logs/sync_{time}.log",
    rotation="1 day",
    retention="30 days",
    level=settings.log_level,
    format="{time} | {level} | {message}"
)
```

### Metrics to Track
- Webhook response time (target: < 1 second)
- Sync success rate (target: > 99%)
- API call latencies (Offorte, Airtable)
- Queue depth (Redis)
- Failed job count

---

## Deployment Configuration

### Environment-Specific Settings

**Development**:
```bash
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
```

**Production**:
```bash
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### Docker Support (Optional)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Quality Checklist

Before implementation:
- [ ] All required API keys identified
- [ ] Single LLM provider (OpenAI) configured
- [ ] Simple dataclass dependencies defined
- [ ] Rate limiting strategy documented
- [ ] Webhook security measures specified
- [ ] Background processing queue configured
- [ ] Testing fixtures defined
- [ ] Logging and monitoring planned
- [ ] Environment variable validation included
- [ ] Resource cleanup handled

---

## Integration Points

### With Other Subagents

**prompt-engineer**:
- Will provide system prompt for `agent.py`
- Needs to understand Offorte/Airtable domain
- Must handle Dutch language terminology

**tool-integrator**:
- Will implement tools using `AgentDependencies`
- Needs access to HTTP client from dependencies
- Must handle rate limiting per API

**pydantic-ai-validator**:
- Will test with `TestModel` and `test_dependencies`
- Validates dependency injection works
- Tests tool parameter validation

---

## Summary

This specification provides a MINIMAL configuration foundation for the Offorte-to-Airtable sync agent:

1. **Essential Environment Variables**: Only what's needed - API keys, base URLs, and basic config
2. **Single LLM Provider**: OpenAI only, no complex fallback logic
3. **Simple Dependencies**: Dataclass with lazy HTTP client initialization
4. **Clear External Services**: Offorte, Airtable, Redis configurations
5. **Basic Security**: API key validation, webhook signatures
6. **Testing Ready**: Fixtures and test configuration included

The implementation follows the main_agent_reference pattern with python-dotenv and pydantic-settings for proper configuration management.
