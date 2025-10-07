---
name: "Offorte-Airtable Sync Agent - Production Implementation PRP"
description: "Comprehensive PRP for building a scalable, configuration-driven Pydantic AI agent that syncs Offorte proposals to Airtable operations systems"
created: "2025-01-07"
sources:
  - "PRPs/INITIAL-Offorte-Airtable-Sync.md"
  - "Offorte-Airtable-Sync-Agent-PRP.md"
  - "FullExample/n8n_workflows/"
  - "PRPs/examples/main_agent_reference/"
confidence_score: "9/10"
---

# Offorte-Airtable Sync Agent - Complete Implementation PRP

## Purpose

Build a production-ready Pydantic AI agent that automatically syncs accepted proposal data from Offorte to Airtable for operations management. The agent must be **scalable and configuration-driven** to support adding new tables and extracting additional proposal fields without code changes.

**Key Innovation**: Unlike the existing n8n workflow (which uses PDF parsing), this agent uses the Offorte API directly for reliable, structured data extraction.

## Core Principles

1. **Pydantic AI Best Practices**: Deep integration with Pydantic AI patterns (follow main_agent_reference)
2. **Configuration-Driven Design**: Table mappings in YAML/JSON, not hardcoded
3. **Type Safety First**: Leverage Pydantic validation throughout
4. **Production Reliability**: Webhooks < 5s response, proper error handling, idempotent operations
5. **Scalability**: Add new tables by updating config, not code

## ⚠️ Implementation Guidelines: Keep It Practical

**IMPORTANT**: Build a focused, scalable agent. Don't over-engineer.

- ✅ **Configuration-driven from day one** - Table mappings in YAML files
- ✅ **Start with 6 tables** - But design for easy expansion
- ✅ **Follow main_agent_reference** - Use proven patterns from examples
- ✅ **Use string output by default** - Only add result_type when validation needed
- ✅ **Test with TestModel** - Validate agent logic without API calls

### Key Question:
**"Can I add a new table without changing Python code?"** - If no, refactor the design.

---

## Goal

Create an automated sync agent that:
1. Receives Offorte webhooks (proposal_won) within 5-second timeout
2. Queues processing jobs in Redis for background execution
3. Fetches complete proposal data from Offorte API
4. Transforms Dutch construction quotes to Airtable schemas
5. Syncs to N tables using configuration-driven mappings
6. Handles errors with retry logic and detailed logging

**Success Metric**: Adding a 7th table requires only creating a new YAML config file, zero code changes.

## Why

**Business Problem**: Manual data entry of accepted proposals takes 30+ minutes and causes errors.

**Solution Value**:
- Eliminates manual data entry (saves 30+ min per proposal)
- Zero data entry errors through automated validation
- Instant visibility in operations systems
- Automatic invoice scheduling (30/65/5 Dutch construction terms)
- **Future-proof**: Easy to add new tables, extract more API fields

**Why Not PDF Parsing**: Existing n8n workflow uses PDF extraction which is brittle and limited. Direct API access provides:
- Structured, reliable data
- Access to all proposal fields (not just PDF content)
- Ability to fetch related resources (contacts, companies)
- Real-time updates on proposal changes

## What

### Agent Type Classification
- [x] **Tool-Enabled Agent**: External API integration (Offorte, Airtable)
- [x] **Workflow Agent**: Multi-step orchestration with error handling
- [ ] Chat Agent: Not needed
- [ ] Structured Output Agent: String output is sufficient (unless specific validation needed)

### External Integrations
- [x] Offorte API (v2) - Proposal data, customer info, line items
- [x] Airtable API - Multi-table sync with pyairtable
- [x] Redis - Job queue for async processing
- [x] Celery - Background task worker
- [x] FastAPI - Webhook receiver endpoint

### Success Criteria
- [ ] Webhook receives and queues events in < 1 second (5s Offorte timeout)
- [ ] Complete proposal sync to 6 tables within 30 seconds
- [ ] Invoice splits calculate correctly (30% vooraf, 65% start, 5% oplevering)
- [ ] Coupled elements (D1, D2 variants) handled as separate records
- [ ] Error handling with 3 retries and exponential backoff
- [ ] Dutch special characters (ë, ï, ö, ü, €) display correctly
- [ ] No duplicate records on re-sync (idempotent operations)
- [ ] **Scalability test**: Add 7th table with only config changes (< 10 minutes)
- [ ] Comprehensive test coverage with TestModel (no real API calls in tests)
- [ ] 99.9% uptime for webhook endpoint

---

## All Needed Context

### Pydantic AI Documentation & Research

```yaml
# ESSENTIAL PYDANTIC AI DOCUMENTATION - Research completed

core_framework:
  - url: https://ai.pydantic.dev/
    why: Official documentation with getting started guide
    key_learnings: |
      - Agent creation with model provider abstraction
      - Default to string output (no result_type unless needed)
      - Use @agent.tool with RunContext for dependency injection
      - Follow main_agent_reference pattern for settings/providers

  - url: https://ai.pydantic.dev/agents/
    why: Agent architecture and configuration patterns
    key_learnings: |
      - Static vs dynamic system prompts
      - Use dynamic prompts with @agent.system_prompt for runtime context
      - Agents are generic and reusable across applications
      - Prefer 'instructions' parameter in many cases

  - url: https://ai.pydantic.dev/tools/
    why: Tool integration patterns
    key_learnings: |
      - @agent.tool for context-aware tools (RunContext[DepsType])
      - @agent.tool_plain for simple tools without context
      - Parameter validation via function signatures and Pydantic models
      - Docstring parsing for tool descriptions (Google/NumPy/Sphinx formats)

  - url: https://ai.pydantic.dev/testing/
    why: Testing strategies for Pydantic AI agents
    key_learnings: |
      - Use TestModel for development (no real API calls)
      - Use FunctionModel for custom behavior simulation
      - Agent.override() for test isolation
      - Set ALLOW_MODEL_REQUESTS=False to prevent accidental API calls
      - Use capture_run_messages() to inspect agent-model interactions

# Prebuilt examples in codebase
local_examples:
  - path: PRPs/examples/main_agent_reference/
    why: Best practices for Pydantic AI agent structure
    key_patterns: |
      - settings.py: pydantic-settings with load_dotenv()
      - providers.py: get_llm_model() function for model abstraction
      - tools.py: Pure functions that agents call via decorators
      - research_agent.py: Agent with multiple tools and dependencies
      - NO result_type used (defaults to string output)

  - path: PRPs/examples/tool_enabled_agent/
    why: External API integration patterns
    key_patterns: |
      - Async HTTP calls with httpx/aiohttp
      - Error handling and retry logic
      - Tool parameter validation with type hints
      - Dependency injection via dataclass

  - path: PRPs/examples/testing_examples/
    why: Comprehensive testing patterns
    key_patterns: |
      - TestModel for rapid validation
      - FunctionModel for custom responses
      - Mock external API calls
      - Agent.override() for test contexts
```

### Offorte API Research (Completed)

```yaml
offorte_api:
  base_url: "https://connect.offorte.com/api/v2/{account_name}"
  authentication: "API Key (simpler than OAuth2)"
  rate_limits:
    requests_per_second: 2
    requests_per_hour: 360

  webhooks:
    timeout: "5 seconds (CRITICAL)"
    events:
      - proposal_won: "Proposal accepted by customer"
      - proposal_details_updated: "Proposal data changed"
    throttling: "Events are batched and deduplicated"
    validation: "Signature-based security (implement validation)"
    payload_structure:
      type: "event_type string"
      date_created: "timestamp"
      data:
        id: "proposal_id"
        status: "won/lost/pending"
        total_price: "float"
        company_id: "int"
        contact_ids: "list[int]"

  key_endpoints:
    get_proposal: "GET /proposals/{id}"
    get_proposal_content: "GET /proposals/{id}/content"
    get_company: "GET /companies/{company_id}"
    get_contact: "GET /contacts/{contact_id}"

  gotchas:
    - "Must respond to webhooks in < 5 seconds or Offorte times out"
    - "Rate limit is strict: 2 req/sec, implement throttling"
    - "Dutch content with special characters (ë, ï, ö, ü)"
    - "Dates in DD-MM-YYYY format"
    - "Currency in €1.234,56 format (period thousands, comma decimal)"

  documentation: "https://www.offorte.com/api-docs"
  mcp_server: "https://github.com/offorte/offorte-mcp-server (reference)"
```

### Airtable API Research (Completed)

```yaml
airtable_api:
  base_url: "https://api.airtable.com/v0/{base_id}/"
  authentication: "Bearer token (API Key)"
  rate_limits:
    requests_per_second: 5
    requests_per_base: "Per base limit"
    batch_size: 10  # Max records per create/update

  python_client: "pyairtable==2.2.0"
  key_operations:
    batch_create: "table.batch_create(records)"
    batch_update: "table.batch_update(records, replace=False)"
    batch_upsert: "table.batch_upsert(records, key_fields=['unique_field'])"

  upsert_strategy:
    method: "batch_upsert with key_fields"
    example: |
      table.batch_upsert(
          [{"fields": {"Order Nummer": "2025001", "Klant": "ABC BV"}}],
          key_fields=["Order Nummer"]
      )
    behavior: "Update if key exists, create if new"

  gotchas:
    - "Rate limit: 5 req/sec - use batch operations"
    - "Max 10 records per batch - chunk larger datasets"
    - "Retry with exponential backoff on 429 errors"
    - "pyairtable handles retries automatically (up to 5 times)"

  documentation:
    - "https://airtable.com/developers/web/api/introduction"
    - "https://pyairtable.readthedocs.io/"
```

### Background Processing Research (Completed)

```yaml
fastapi_celery_redis_pattern:
  architecture: |
    FastAPI (webhook) → Redis (queue) → Celery Worker (processing)

  implementation:
    webhook_endpoint:
      response_time: "< 1 second (Offorte timeout is 5s)"
      action: "Validate, queue to Redis, return 200 immediately"
      never: "Don't process inline, don't call external APIs"

    redis_queue:
      purpose: "Decouple webhook from processing"
      data: "Minimal - just proposal_id and event_type"
      persistence: "Configure Redis persistence for reliability"

    celery_worker:
      execution: "Async background processing"
      concurrency: "Multiple workers for parallel processing"
      retry: "Automatic retry with exponential backoff"
      monitoring: "Flower dashboard for task visibility"

  production_setup:
    processes: ["FastAPI server", "Redis server", "Celery worker"]
    containerization: "Docker Compose for all services"
    monitoring: "Flower (Celery UI) + custom logging"

  gotchas:
    - "Always respond to webhook immediately (< 5s)"
    - "Queue lightweight payloads (just IDs, not full data)"
    - "Celery tasks should be idempotent"
    - "Configure Redis persistence for durability"

  documentation:
    - "https://fastapi.tiangolo.com/tutorial/background-tasks/"
    - "https://testdriven.io/blog/fastapi-and-celery/"
    - "https://docs.celeryq.dev/"
```

### Configuration-Driven Architecture Design

```yaml
scalability_approach:
  problem: "Hardcoded table mappings don't scale"
  solution: "Configuration-driven mapping with plugin architecture"

  config_structure:
    location: "config/table_mappings/"
    format: "YAML files (one per table or group)"
    loading: "Dynamic at runtime"
    validation: "Pydantic models for config schemas"

  example_config:
    file: "config/table_mappings/klantenportaal.yaml"
    content: |
      table_name: "klantenportaal"
      base_id: "${AIRTABLE_BASE_ADMINISTRATION}"
      key_field: "Offerte Nummer"

      field_mappings:
        "Bedrijfsnaam":
          source: "company.name"
          required: true
        "Adres":
          source: "company.street"
          required: false
        "Postcode":
          source: "company.zipcode"
          transform: "uppercase"
        "Email":
          source: "company.email"
          validation: "email"

      relationships:
        - target_table: "projecten"
          link_field: "Klant"
          match_on: "Bedrijfsnaam"

  transformation_functions:
    registry: "config/transformations.py"
    example: |
      TRANSFORMATIONS = {
          "invoice_splits": calculate_invoice_splits,
          "element_parsing": parse_construction_elements,
          "date_add_days": lambda date, days: date + timedelta(days=days)
      }

  adding_new_table:
    steps:
      1. "Create config/table_mappings/new_table.yaml"
      2. "Define field_mappings and transformations"
      3. "Register custom transforms if needed"
      4. "Restart worker (config loaded dynamically)"
    time_estimate: "5-10 minutes"
    code_changes: "ZERO (unless custom transform needed)"
```

### Data Mapping Specifications (From Existing Spec)

```yaml
# These are the INITIAL 6 tables - but system must support adding more via config

table_1_klantenportaal:
  purpose: "Customer portal information"
  base: "${AIRTABLE_BASE_ADMINISTRATION}"
  key_field: "Offerte Nummer"
  mappings:
    "Bedrijfsnaam": "company.name"
    "Adres": "company.street"
    "Postcode": "company.zipcode"
    "Plaats": "company.city"
    "Email": "company.email"
    "Telefoon": "company.phone"
    "Contact Persoon": "contacts[0].name"
    "Offerte Nummer": "proposal_nr"
    "Status": "'Actief'"  # Static value

table_2_projecten:
  purpose: "Overall project administration"
  base: "${AIRTABLE_BASE_ADMINISTRATION}"
  key_field: "Project Nummer"
  mappings:
    "Project Nummer": "proposal_nr"
    "Naam": "name"
    "Klant": "company.name"
    "Totaal Bedrag": "total_price"
    "Start Datum": "project_date"
    "Eind Datum": "project_date + 60 days"
    "Status": "'Gewonnen'"
    "Verantwoordelijke": "account_user_name"
    "Offorte ID": "id"

table_3_elementen_review:
  purpose: "Individual construction elements"
  base: "${AIRTABLE_BASE_SALES}"
  key_field: "Element ID"
  source: "Extracted from proposal content (parse_construction_elements)"
  mappings:
    "Order Nummer": "proposal_nr"
    "Element ID": "f'{proposal_nr}_{element_index}'"
    "Type": "element.type"  # e.g., "Draaikiep raam"
    "Merk": "element.brand"  # e.g., "Merk 1"
    "Locatie": "element.location"
    "Breedte (mm)": "element.width"
    "Hoogte (mm)": "element.height"
    "Gekoppeld": "element.coupled"  # True if D1/D2
    "Variant": "element.variant"  # "D1", "D2", etc.
    "Prijs": "element.price"
    "Opmerkingen": "element.notes"
  parsing_rules:
    - "Look for 'Merk {n}:' blocks"
    - "D1. D2. means two separate coupled elements"
    - "Extract dimensions like '1200x2400mm'"

table_4_facturatie:
  purpose: "Invoice records (3 per project)"
  base: "${AIRTABLE_BASE_ADMINISTRATION}"
  key_field: "Factuur ID"
  source: "Generated (calculate_invoice_splits)"
  records: 3  # Always create 3 invoices
  splits:
    - percentage: 30
      type: "30% - Vooraf"
      date: "today"
      status: "Concept"
    - percentage: 65
      type: "65% - Start"
      date: "project_date"
      status: "Gepland"
    - percentage: 5
      type: "5% - Oplevering"
      date: "project_date + 60 days"
      status: "Gepland"

table_5_inmeetplanning:
  purpose: "Measurement planning schedule"
  base: "${AIRTABLE_BASE_TECHNICAL}"
  key_field: "Order Nummer"
  mappings:
    "Order Nummer": "proposal_nr"
    "Klant": "company.name"
    "Aantal Elementen": "len(elements)"
    "Geschatte Tijd (min)": "len(elements) * 18"  # 18 min per element
    "Geplande Datum": "measurement_date"
    "Status": "'Te plannen'"
    "Toegewezen aan": "null"  # Manual assignment

table_6_deur_specificaties:
  purpose: "Door-specific details"
  base: "${AIRTABLE_BASE_TECHNICAL}"
  key_field: "Order Nummer + Deur Type"
  filter: "Only for door elements"
  mappings:
    "Order Nummer": "proposal_nr"
    "Deur Type": "element.door_type"
    "Model": "element.model"
    "Kleur": "element.color"
    "Glastype": "element.glass_type"
    "Sluitwerk": "element.locks"
    "Speciale Kenmerken": "element.special_features"

# Future tables (examples) - add via config only
future_tables:
  - "leveranciers": "Supplier information"
  - "productie_planning": "Production scheduling"
  - "transport_planning": "Delivery logistics"
```

### Common Pydantic AI Gotchas (Research Completed)

```yaml
implementation_gotchas:
  async_patterns:
    issue: "Mixing sync and async agent calls inconsistently"
    solution: |
      - Use async/await consistently throughout
      - Agent.run() for async, agent.run_sync() for sync contexts
      - All tools calling external APIs should be async
      - Use httpx.AsyncClient for HTTP calls, not requests

  dependency_complexity:
    issue: "Complex dependency graphs are hard to debug"
    solution: |
      - Keep dependencies simple and flat
      - Use dataclasses for dependency typing
      - Avoid circular dependencies
      - Inject external services, not tool instances

  tool_error_handling:
    issue: "Tool failures can crash entire agent runs"
    solution: |
      - Wrap tool logic in try/except
      - Return error dictionaries instead of raising
      - Implement retry logic with exponential backoff
      - Log all errors with context

  rate_limiting:
    issue: "External APIs have strict rate limits"
    solution: |
      - Implement throttling for Offorte (2 req/sec)
      - Use batch operations for Airtable (max 10 records)
      - Add delays between requests
      - Queue requests when approaching limits

  model_string_antipattern:
    issue: "Hardcoding model strings like 'openai:gpt-4o'"
    solution: |
      - Follow main_agent_reference pattern
      - Use get_llm_model() from providers.py
      - Configure via environment variables
      - Support multiple providers
```

---

## Implementation Blueprint

### Technology Research Phase

**RESEARCH COMPLETED** ✅

All necessary research has been completed for:
- ✅ Pydantic AI framework deep dive (agents, tools, testing)
- ✅ Offorte API endpoints, webhooks, rate limits
- ✅ Airtable API with pyairtable batch operations
- ✅ FastAPI + Celery + Redis background processing pattern
- ✅ Configuration-driven architecture design
- ✅ Dutch language handling (€, special chars, date formats)

### Agent Architecture Planning

```yaml
project_structure:
  offorte_airtable_sync/
    ├── config/
    │   ├── table_mappings/
    │   │   ├── klantenportaal.yaml
    │   │   ├── projecten.yaml
    │   │   ├── elementen_review.yaml
    │   │   ├── facturatie.yaml
    │   │   ├── inmeetplanning.yaml
    │   │   └── deur_specificaties.yaml
    │   ├── transformations.py        # Custom transform functions
    │   └── mapping_schema.py         # Pydantic models for config validation
    │
    ├── agent/
    │   ├── __init__.py
    │   ├── settings.py               # Environment config (pydantic-settings)
    │   ├── providers.py              # get_llm_model() function
    │   ├── models.py                 # Pydantic models for data validation
    │   ├── dependencies.py           # SyncAgentDependencies dataclass
    │   ├── sync_agent.py             # Main agent definition
    │   └── tools.py                  # Agent tool functions
    │
    ├── core/
    │   ├── __init__.py
    │   ├── offorte_client.py         # Offorte API wrapper
    │   ├── airtable_client.py        # Airtable API wrapper (pyairtable)
    │   ├── config_loader.py          # Load and validate YAML configs
    │   ├── field_mapper.py           # Apply field mappings from config
    │   ├── transformations.py        # Data transformation logic
    │   └── parsers.py                # Dutch construction element parsing
    │
    ├── api/
    │   ├── __init__.py
    │   ├── webhook.py                # FastAPI webhook endpoint
    │   └── models.py                 # FastAPI request/response models
    │
    ├── tasks/
    │   ├── __init__.py
    │   ├── celery_app.py             # Celery configuration
    │   └── sync_tasks.py             # Background processing tasks
    │
    ├── tests/
    │   ├── __init__.py
    │   ├── conftest.py               # pytest fixtures
    │   ├── test_agent.py             # Agent tests with TestModel
    │   ├── test_tools.py             # Tool validation tests
    │   ├── test_config_loader.py    # Config loading tests
    │   ├── test_field_mapper.py     # Mapping logic tests
    │   ├── test_parsers.py           # Element parsing tests
    │   └── fixtures/
    │       ├── sample_proposal.json
    │       └── sample_configs.yaml
    │
    ├── .env.example
    ├── requirements.txt
    ├── docker-compose.yml
    └── README.md
```

### Implementation Task Breakdown

```yaml
Phase 1: Foundation & Configuration System
  duration: "Day 1-2"
  tasks:
    - task: "Setup project structure and dependencies"
      files: ["requirements.txt", "pyproject.toml", ".env.example"]
      validation: "pip install works, imports succeed"

    - task: "Create configuration schema and loader"
      files: ["config/mapping_schema.py", "core/config_loader.py"]
      validation: "Can load and validate YAML configs"
      tests: ["test_config_loader.py"]

    - task: "Implement settings and providers (follow main_agent_reference)"
      files: ["agent/settings.py", "agent/providers.py"]
      validation: "get_llm_model() returns configured model"
      tests: ["test_settings.py", "test_providers.py"]

Phase 2: External API Clients
  duration: "Day 2-3"
  tasks:
    - task: "Build Offorte API client with rate limiting"
      files: ["core/offorte_client.py"]
      features: ["fetch_proposal", "fetch_company", "fetch_contacts", "throttling"]
      validation: "Can fetch proposal data from Offorte API"
      tests: ["test_offorte_client.py (mocked)"]

    - task: "Build Airtable API client with batch operations"
      files: ["core/airtable_client.py"]
      features: ["batch_create", "batch_upsert", "rate_limit handling"]
      validation: "Can sync records to Airtable with upsert"
      tests: ["test_airtable_client.py (mocked)"]

Phase 3: Data Transformation Pipeline
  duration: "Day 3-4"
  tasks:
    - task: "Implement Dutch construction element parser"
      files: ["core/parsers.py"]
      features: ["parse Merk blocks", "handle coupled elements D1/D2", "extract dimensions"]
      validation: "Correctly parses sample Dutch proposal content"
      tests: ["test_parsers.py (with real examples)"]

    - task: "Build configuration-driven field mapper"
      files: ["core/field_mapper.py"]
      features: ["apply YAML mappings", "nested field access", "call transformations"]
      validation: "Maps proposal data to Airtable records per config"
      tests: ["test_field_mapper.py"]

    - task: "Implement transformation functions"
      files: ["core/transformations.py", "config/transformations.py"]
      features: ["invoice_splits", "date calculations", "element grouping"]
      validation: "Invoice splits calculate correctly (30/65/5)"
      tests: ["test_transformations.py"]

Phase 4: Pydantic AI Agent
  duration: "Day 4-5"
  tasks:
    - task: "Create agent dependencies and models"
      files: ["agent/dependencies.py", "agent/models.py"]
      content: "SyncAgentDependencies dataclass with all external services"
      validation: "Dependencies instantiate correctly"

    - task: "Implement agent tools"
      files: ["agent/tools.py"]
      tools:
        - "validate_webhook(payload, signature) -> dict"
        - "fetch_proposal_data(proposal_id, include_fields) -> dict"
        - "parse_construction_elements(content, rules) -> list"
        - "transform_proposal_to_table_records(data, config) -> dict"
        - "sync_to_airtable(base_id, table, records, key_field) -> dict"
        - "process_won_proposal(proposal_id, sync_config) -> dict"
      validation: "Each tool works independently"
      tests: ["test_tools.py (mocked external calls)"]

    - task: "Define main sync agent"
      files: ["agent/sync_agent.py"]
      pattern: "Follow main_agent_reference (no result_type, string output)"
      validation: "Agent instantiates and tools register correctly"
      tests: ["test_agent.py (with TestModel)"]

Phase 5: Webhook & Background Processing
  duration: "Day 5-6"
  tasks:
    - task: "Build FastAPI webhook receiver"
      files: ["api/webhook.py", "api/models.py"]
      features: ["signature validation", "Redis queueing", "< 1s response time"]
      validation: "Webhook responds in < 1 second"
      tests: ["test_webhook.py"]

    - task: "Setup Celery background worker"
      files: ["tasks/celery_app.py", "tasks/sync_tasks.py"]
      features: ["agent invocation", "retry logic", "error handling"]
      validation: "Background task processes proposal successfully"
      tests: ["test_sync_tasks.py"]

Phase 6: Configuration Files & Testing
  duration: "Day 6-7"
  tasks:
    - task: "Create all 6 table mapping configs"
      files: ["config/table_mappings/*.yaml"]
      validation: "All configs validate against schema"
      tests: ["Mapping configs load without errors"]

    - task: "Comprehensive integration testing"
      files: ["tests/test_integration.py"]
      tests:
        - "End-to-end sync with mocked APIs"
        - "Error scenarios (API failures, invalid data)"
        - "Scalability test: add 7th table via config only"
      validation: "All integration tests pass"

    - task: "Performance and reliability testing"
      tests:
        - "Webhook response time < 1 second"
        - "Complete sync < 30 seconds"
        - "Handles rate limits gracefully"
        - "Idempotent operations (no duplicates on re-sync)"

Phase 7: Production Deployment
  duration: "Day 7"
  tasks:
    - task: "Create Docker Compose setup"
      files: ["docker-compose.yml", "Dockerfile"]
      services: ["fastapi", "celery worker", "redis", "flower (monitoring)"]
      validation: "docker-compose up works"

    - task: "Documentation and deployment guide"
      files: ["README.md", "DEPLOYMENT.md"]
      content: ["Setup instructions", "Configuration guide", "Monitoring"]
```

### Pseudocode: Core Processing Flow

```python
# File: agent/sync_agent.py
from pydantic_ai import Agent, RunContext
from .providers import get_llm_model
from .dependencies import SyncAgentDependencies

SYSTEM_PROMPT = """
You are an integration automation agent that syncs accepted proposals
from Offorte to Airtable operations systems.

Your responsibilities:
- Process webhook events from Offorte within 5 seconds
- Fetch complete proposal data including all line items
- Transform Dutch construction quotes to Airtable operational schemas
- Create records across multiple tables using configuration-driven mappings
- Calculate Dutch construction payment splits (30% vooraf, 65% start, 5% oplevering)
- Handle errors gracefully with retry logic

Data handling rules:
- Parse "Merk" blocks to identify construction elements
- Treat coupled variants (D1, D2) as separate records
- Handle Dutch special characters (ë, ï, ö, ü) and € formatting
- Use upsert logic to prevent duplicates
- Load table mappings from configuration files
"""

# Create agent (follow main_agent_reference pattern)
sync_agent = Agent(
    get_llm_model(),  # From providers.py
    deps_type=SyncAgentDependencies,
    system_prompt=SYSTEM_PROMPT
)


@sync_agent.tool
async def process_won_proposal(
    ctx: RunContext[SyncAgentDependencies],
    proposal_id: int,
    sync_config_path: str = "config/table_mappings/"
) -> dict:
    """
    End-to-end orchestration tool for syncing won proposals.
    """
    try:
        # Step 1: Load table configurations dynamically
        table_configs = load_table_configs(sync_config_path)

        # Step 2: Fetch complete proposal data from Offorte
        proposal_data = await ctx.deps.offorte_client.fetch_proposal(
            proposal_id,
            include_fields=get_required_fields(table_configs)
        )

        # Step 3: Parse construction elements
        elements = parse_construction_elements(
            proposal_data.get("content", {}),
            extraction_rules=load_extraction_rules()
        )

        # Step 4: Transform to table records using configs
        all_records = {}
        for table_name, config in table_configs.items():
            records = transform_proposal_to_table_records(
                proposal_data,
                elements,
                config
            )
            all_records[table_name] = records

        # Step 5: Sync to Airtable (batch operations)
        sync_results = {}
        for table_name, records in all_records.items():
            config = table_configs[table_name]
            result = await sync_to_airtable(
                ctx,
                base_id=config["base_id"],
                table_name=table_name,
                records=records,
                key_field=config.get("key_field")
            )
            sync_results[table_name] = result

        # Step 6: Return comprehensive report
        return {
            "status": "success",
            "proposal_id": proposal_id,
            "tables_synced": len(sync_results),
            "total_records_created": sum(r["created"] for r in sync_results.values()),
            "total_records_updated": sum(r["updated"] for r in sync_results.values()),
            "details": sync_results
        }

    except Exception as e:
        logger.error(f"Sync failed for proposal {proposal_id}: {e}")
        return {
            "status": "error",
            "proposal_id": proposal_id,
            "error": str(e)
        }


# File: core/field_mapper.py
def transform_proposal_to_table_records(
    proposal_data: dict,
    elements: list[dict],
    config: dict
) -> list[dict]:
    """
    Apply configuration-driven field mappings.

    Config structure:
    {
        "mappings": {
            "Airtable Field": "proposal.nested.field",
            "Another Field": "static_value"
        },
        "transformation": "invoice_splits",  # Optional custom function
        "filter": "lambda el: el.type == 'door'"  # Optional filter
    }
    """
    records = []

    # Check if transformation function needed
    if "transformation" in config:
        transform_func = TRANSFORMATIONS[config["transformation"]]
        return transform_func(proposal_data, elements, config)

    # Apply standard field mappings
    for mapping in config.get("mappings", {}):
        airtable_field = mapping["airtable_field"]
        source_path = mapping["source"]

        # Extract value from nested path (e.g., "company.name")
        value = get_nested_value(proposal_data, source_path)

        # Apply any transforms (uppercase, date format, etc.)
        if "transform" in mapping:
            value = apply_transform(value, mapping["transform"])

        record = {"fields": {airtable_field: value}}
        records.append(record)

    return records


# File: tasks/sync_tasks.py
from celery import Celery
from agent.sync_agent import sync_agent
from agent.dependencies import SyncAgentDependencies

celery_app = Celery('offorte_sync', broker='redis://localhost:6379')

@celery_app.task(bind=True, max_retries=3)
def sync_proposal_task(self, proposal_id: int):
    """
    Celery task that runs the Pydantic AI agent.
    """
    try:
        # Create dependencies
        deps = create_agent_dependencies()

        # Run agent
        result = sync_agent.run_sync(
            f"Process won proposal {proposal_id}",
            deps=deps
        )

        return result.data

    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


# File: api/webhook.py
from fastapi import FastAPI, Request
from tasks.sync_tasks import sync_proposal_task

app = FastAPI()

@app.post("/webhook/offorte")
async def receive_webhook(request: Request):
    """
    Webhook receiver - MUST respond in < 5 seconds.
    """
    payload = await request.json()

    # Validate signature (security)
    if not validate_webhook_signature(payload, request.headers):
        return {"error": "Invalid signature"}, 401

    # Queue for async processing (don't process inline!)
    if payload["type"] == "proposal_won":
        sync_proposal_task.delay(payload["data"]["id"])

    # Return immediately (< 1 second)
    return {"status": "accepted"}
```

---

## Validation Loop

### Level 1: Project Structure & Configuration

```bash
# Verify project structure
ls -R offorte_airtable_sync/ | grep -E "(agent|core|api|tasks|config|tests)"

# Verify configuration files exist
find config/table_mappings -name "*.yaml"

# Validate YAML configs against schema
python -c "
from core.config_loader import load_table_configs
configs = load_table_configs('config/table_mappings/')
print(f'Loaded {len(configs)} table configurations')
"

# Expected: All 6 table configs load successfully
# If failing: Fix YAML syntax or schema validation errors
```

### Level 2: Agent & Tools Validation

```bash
# Test agent instantiation
python -c "
from agent.sync_agent import sync_agent
from agent.providers import get_llm_model
print(f'Agent created with model: {sync_agent.model}')
print(f'Registered tools: {len(sync_agent.tools)}')
"

# Test with TestModel (no real API calls)
python -c "
from pydantic_ai.models.test import TestModel
from agent.sync_agent import sync_agent
from agent.dependencies import SyncAgentDependencies

test_model = TestModel()
deps = SyncAgentDependencies(
    offorte_api_key='test',
    offorte_account_name='test',
    airtable_api_key='test',
    # ... other test deps
)

with sync_agent.override(model=test_model):
    result = sync_agent.run_sync('Test message', deps=deps)
    print(f'Agent response: {result.data[:100]}...')
"

# Expected: Agent instantiates, tools register, TestModel validation passes
# If failing: Check tool registration, dependency types, model configuration
```

### Level 3: Tool Function Tests

```bash
# Run tool-specific tests
pytest tests/test_tools.py -v

# Test specific tools
pytest tests/test_tools.py::test_fetch_proposal_data -v
pytest tests/test_tools.py::test_parse_construction_elements -v
pytest tests/test_tools.py::test_sync_to_airtable -v

# Expected: All tool tests pass with mocked external APIs
# If failing: Fix tool logic, parameter validation, error handling
```

### Level 4: Configuration-Driven Mapping

```bash
# Test field mapper with sample data
pytest tests/test_field_mapper.py -v

# Test transformation functions
pytest tests/test_transformations.py -v

# Verify invoice split calculations
python -c "
from core.transformations import calculate_invoice_splits
invoices = calculate_invoice_splits(total_amount=45000.0, project_date='2025-02-01')
assert len(invoices) == 3
assert invoices[0]['amount'] == 13500.0  # 30%
assert invoices[1]['amount'] == 29250.0  # 65%
assert invoices[2]['amount'] == 2250.0   # 5%
print('Invoice splits correct!')
"

# Expected: All mappings and transformations work correctly
# If failing: Check mapping logic, transformation functions
```

### Level 5: Integration Tests

```bash
# Run full integration test suite
pytest tests/test_integration.py -v

# Test end-to-end sync with mocked APIs
pytest tests/test_integration.py::test_full_proposal_sync -v

# Test error scenarios
pytest tests/test_integration.py::test_api_failure_retry -v
pytest tests/test_integration.py::test_invalid_proposal_data -v

# Expected: Complete sync workflow works with mocked external services
# If failing: Check orchestration logic, error handling, retry mechanisms
```

### Level 6: Scalability Test (CRITICAL)

```bash
# Test adding a 7th table via config only (no code changes)
cat > config/table_mappings/leveranciers.yaml << EOF
table_name: "leveranciers"
base_id: "\${AIRTABLE_BASE_ADMINISTRATION}"
key_field: "Leverancier Naam"

field_mappings:
  "Leverancier Naam":
    source: "supplier.name"
    required: true
  "Contact Email":
    source: "supplier.email"
    required: false
EOF

# Verify new table loads
python -c "
from core.config_loader import load_table_configs
configs = load_table_configs('config/table_mappings/')
assert 'leveranciers' in configs
print(f'SUCCESS: Loaded {len(configs)} tables including new leveranciers table')
"

# Run sync with new table included
pytest tests/test_scalability.py::test_add_new_table_via_config -v

# Expected: New table syncs without any code changes
# If failing: Configuration system is not truly dynamic
```

### Level 7: Performance & Reliability

```bash
# Test webhook response time
pytest tests/test_webhook.py::test_response_time -v
# Expected: < 1 second response time

# Test complete sync duration
pytest tests/test_performance.py::test_full_sync_duration -v
# Expected: < 30 seconds for complete 6-table sync

# Test rate limiting
pytest tests/test_rate_limiting.py -v
# Expected: Handles Offorte (2/sec) and Airtable (5/sec) limits

# Test idempotency
pytest tests/test_idempotency.py::test_no_duplicates_on_resync -v
# Expected: Re-syncing same proposal doesn't create duplicates
```

### Level 8: Production Readiness

```bash
# Test Docker setup
docker-compose up -d
docker-compose ps
# Expected: All services (fastapi, celery, redis, flower) running

# Test webhook endpoint
curl -X POST http://localhost:8000/webhook/offorte \
  -H "Content-Type: application/json" \
  -d '{"type": "proposal_won", "data": {"id": 12345}}'
# Expected: {"status": "accepted"} in < 1 second

# Check Celery worker
docker-compose logs celery
# Expected: Worker ready, processing tasks

# Check Flower monitoring
curl http://localhost:5555/api/workers
# Expected: Worker status visible

# Verify environment configuration
python -c "
from agent.settings import settings
assert settings.offorte_api_key
assert settings.airtable_api_key
print('Environment configured correctly')
"
```

---

## Final Validation Checklist

### Agent Implementation Completeness

- [ ] Complete project structure with agent/, core/, api/, tasks/, config/, tests/
- [ ] Configuration-driven table mappings (YAML files for each table)
- [ ] Agent instantiation with get_llm_model() from providers.py
- [ ] All 6 tools implemented and registered (@agent.tool decorators)
- [ ] SyncAgentDependencies dataclass with all external services
- [ ] Comprehensive test suite with TestModel (no real API calls in unit tests)

### Pydantic AI Best Practices

- [ ] Follows main_agent_reference pattern (settings.py, providers.py, tools.py)
- [ ] Default string output (no result_type unless specifically needed)
- [ ] Type safety with proper type hints and Pydantic validation
- [ ] Async/await patterns consistent throughout
- [ ] Error handling with try/except and proper error messages
- [ ] Tools use RunContext[SyncAgentDependencies] for dependency injection

### External API Integration

- [ ] Offorte client with rate limiting (2 req/sec, 360/hour)
- [ ] Airtable client with batch operations (max 10 records)
- [ ] pyairtable batch_upsert for idempotent operations
- [ ] Retry logic with exponential backoff (2s, 4s, 8s)
- [ ] Proper error handling for API failures

### Background Processing

- [ ] FastAPI webhook responds in < 1 second
- [ ] Redis queueing for async processing
- [ ] Celery worker with retry logic
- [ ] Flower dashboard for monitoring
- [ ] Docker Compose setup for all services

### Configuration & Scalability

- [ ] **CRITICAL**: Table mappings in YAML config files (not hardcoded)
- [ ] **CRITICAL**: Can add 7th table with only config changes (< 10 min, zero code)
- [ ] Configuration validation with Pydantic schemas
- [ ] Dynamic config loading at runtime
- [ ] Transformation function registry
- [ ] Extraction rules configurable

### Data Handling

- [ ] Dutch special characters (ë, ï, ö, ü) handled correctly
- [ ] € currency formatting preserved (1.234,56 format)
- [ ] Date format DD-MM-YYYY
- [ ] Construction element parsing (Merk blocks)
- [ ] Coupled elements (D1, D2) as separate records
- [ ] Invoice splits (30/65/5) calculate correctly
- [ ] 18 minutes per element calculation

### Testing & Reliability

- [ ] TestModel integration for agent logic validation
- [ ] Mocked external API calls in tests
- [ ] Integration tests for end-to-end flow
- [ ] Error scenario testing (API failures, invalid data)
- [ ] Performance tests (response time, sync duration)
- [ ] Idempotency tests (no duplicates on re-sync)

### Production Deployment

- [ ] Environment configuration with .env validation
- [ ] Docker Compose for containerized deployment
- [ ] Logging with correlation IDs
- [ ] Monitoring dashboard (Flower)
- [ ] Documentation (README, DEPLOYMENT guide)
- [ ] Security (webhook signature validation, API keys in env)

### Full Readiness

- [ ] Webhook endpoint operational (< 1s response)
- [ ] Complete sync < 30 seconds
- [ ] Rate limiting handled gracefully
- [ ] Error retry with exponential backoff
- [ ] No data loss (idempotent operations)
- [ ] Scalability validated (new table via config only)
- [ ] All tests passing (unit, integration, performance)

---

## Anti-Patterns to Avoid

### Pydantic AI Agent Development

- ❌ Don't skip TestModel validation - ALWAYS test with TestModel during development
- ❌ Don't hardcode API keys - use environment variables with pydantic-settings
- ❌ Don't use hardcoded model strings like "openai:gpt-4o" - use get_llm_model()
- ❌ Don't ignore async patterns - be consistent with async/await throughout
- ❌ Don't create complex tool chains - keep tools focused and composable
- ❌ Don't skip error handling - implement retry and fallback mechanisms
- ❌ Don't use result_type unless structured validation is specifically needed

### Configuration & Scalability

- ❌ **Don't hardcode table mappings** - use YAML config files
- ❌ **Don't hardcode table names** - load dynamically from config directory
- ❌ **Don't hardcode field mappings** - define in config files
- ❌ **Don't hardcode transformation logic** - use plugin/registry pattern
- ❌ Don't require code changes to add new tables - validate config-driven approach

### API Integration

- ❌ Don't process webhooks synchronously - queue immediately to Redis
- ❌ Don't call external APIs in webhook handler - respond in < 1 second
- ❌ Don't ignore rate limits - implement throttling (Offorte: 2/sec, Airtable: 5/sec)
- ❌ Don't skip batch operations - use Airtable batch_upsert (max 10 records)
- ❌ Don't forget retry logic - exponential backoff on failures
- ❌ Don't skip idempotency - use key_fields for upsert, prevent duplicates

### Testing & Deployment

- ❌ Don't test with real APIs in unit tests - use TestModel and mocks
- ❌ Don't skip integration tests - test end-to-end flow
- ❌ Don't skip scalability tests - validate config-driven architecture
- ❌ Don't skip performance tests - webhook < 1s, sync < 30s
- ❌ Don't deploy without monitoring - use Flower and logging

---

## RESEARCH STATUS: ✅ COMPLETED

Comprehensive research completed for:
- ✅ Pydantic AI framework (agents, tools, testing, best practices)
- ✅ Offorte API (webhooks, rate limits, endpoints, authentication)
- ✅ Airtable API (pyairtable, batch operations, upsert logic)
- ✅ FastAPI + Celery + Redis (background processing patterns)
- ✅ Configuration-driven architecture (YAML mappings, plugin system)
- ✅ Dutch language handling (special chars, currency, dates)
- ✅ Existing codebase patterns (main_agent_reference, tool_enabled_agent)

**Agent is ready for implementation following this PRP.**

---

## PRP Quality Score: 9/10

**Confidence for One-Pass Implementation: HIGH**

✅ **Strengths:**
- Complete research with all necessary context
- Configuration-driven design for scalability
- Clear implementation tasks with validation gates
- Follows proven Pydantic AI patterns (main_agent_reference)
- Executable validation commands
- Comprehensive testing strategy
- Production deployment plan

⚠️ **Minor Unknowns:**
- Exact Offorte API response schemas (will need to inspect during implementation)
- Airtable table IDs and exact field names (will need from user)
- Specific Dutch proposal content structure (will test with real examples)

**Mitigation**: These are environmental specifics, not architectural unknowns. The implementation approach handles variability through configuration.

**Why 9/10**: One point deducted only for minor environmental specifics that require user input during implementation. All architectural and technical decisions are well-researched and documented.
