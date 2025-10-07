## FEATURE:

Build an automated Pydantic AI agent that syncs accepted proposal data from Offorte to Airtable for operations management. The agent listens for Offorte webhook events (proposal_won), fetches complete proposal data via API, transforms it to match Airtable schemas, and creates/updates records across 6 operational tables.

**Business Value**:
- Eliminates 30+ minutes of manual data entry per accepted proposal
- Zero data entry errors through automated validation
- Instant visibility of won proposals in operations systems
- Automatic invoice scheduling (30/65/5 payment splits)

**Core Flow**:
1. Customer accepts proposal in Offorte → Webhook fires (proposal_won event)
2. FastAPI endpoint receives webhook → Queues job in Redis (< 5 second response required)
3. Background worker fetches complete proposal data from Offorte API
4. Agent transforms Dutch construction quote data to Airtable schema
5. Syncs to 6 Airtable tables with proper field mapping
6. Updates Offorte with sync status confirmation

## TOOLS:

**IMPORTANT: Design for scalability** - The agent should support adding new tables and extracting additional Offorte data fields without code changes. Use configuration-driven mapping instead of hardcoded table logic.

The agent needs the following tools:

**1. `validate_webhook(payload: dict, signature: str) -> dict`**
- Validates Offorte webhook signature for security
- Parses event type and proposal ID
- Returns: `{"valid": bool, "event_type": str, "proposal_id": int}`

**2. `fetch_proposal_data(proposal_id: int, include_fields: list[str] = None) -> dict`**
- Fetches complete proposal from Offorte API (v2)
- **Scalable**: `include_fields` parameter allows requesting additional API data as needs grow
- Includes: proposal details, line items, customer/contact info, custom fields
- Handles rate limiting (2 req/sec, 360/hour)
- Returns: Complete proposal object with nested data

**3. `parse_construction_elements(proposal_content: dict, extraction_rules: dict = None) -> list[dict]`**
- **Scalable**: Extraction rules can be configured externally
- Identifies "Merk" blocks (e.g., "Merk 1: Voordeur")
- Parses coupled elements (D1, D2 variants mean separate doors)
- Extracts dimensions, types, locations, pricing
- **Future-proof**: Can extract custom fields based on rules
- Returns: List of normalized element dictionaries

**4. `transform_proposal_to_table_records(proposal_data: dict, mapping_config: dict) -> dict`**
- **SCALABLE CORE TOOL** - Transforms Offorte data to Airtable records using configuration
- `mapping_config` defines: table_name, field_mappings, transformations, conditional logic
- Handles multiple destination tables from single config
- Supports custom transformation functions (invoice splits, date calculations, etc.)
- Returns: `{"table_name": [list of records]}`

**5. `sync_to_airtable(base_id: str, table_name: str, records: list[dict], key_field: str = None) -> dict`**
- **Generic sync tool** - Works with any table configuration
- Creates/updates records in Airtable using pyairtable
- Implements batch operations (max 10 records per request)
- Upsert logic using key_field to prevent duplicates
- Handles rate limiting (5 req/sec per base)
- Retry with exponential backoff on failures
- Returns: `{"created": int, "updated": int, "failed": int, "record_ids": list}`

**6. `process_won_proposal(proposal_id: int, sync_config: dict = None) -> dict`**
- **Orchestration tool with configurable pipeline**
- Executes: fetch → parse → transform (using config) → sync to N tables → confirm
- `sync_config` defines which tables to sync and their mappings (defaults to current 6 tables)
- **Easy to extend**: Add new tables by updating configuration, not code
- Handles errors gracefully with detailed logging
- Returns: Complete sync report with status for each table

## DEPENDENCIES

**Pydantic AI RunContext needs:**

```python
@dataclass
class SyncAgentDependencies:
    # Offorte API
    offorte_api_key: str
    offorte_account_name: str
    offorte_base_url: str  # https://connect.offorte.com/api/v2/{account}

    # Airtable API
    airtable_api_key: str
    airtable_base_administration: str  # Base ID for admin tables
    airtable_base_sales: str
    airtable_base_technical: str

    # HTTP client for async requests
    http_client: httpx.AsyncClient

    # Redis queue for webhook processing
    redis_client: Redis

    # Session tracking
    session_id: Optional[str] = None
```

**Configuration Management (for scalability):**
- Store table mappings in YAML/JSON config files (e.g., `table_mappings.yaml`)
- Configuration includes: table names, field mappings, transformation rules, validation schemas
- Adding new tables = update config file, no code changes required
- Example structure:
```yaml
tables:
  klantenportaal:
    base_id: ${AIRTABLE_BASE_ADMINISTRATION}
    key_field: "Offerte Nummer"
    mappings:
      "Bedrijfsnaam": "company.name"
      "Adres": "company.street"
      # ... more fields
  facturatie:
    base_id: ${AIRTABLE_BASE_ADMINISTRATION}
    key_field: "Order Nummer"
    transformation: "invoice_splits"  # Custom function
    # ... mappings
```

**External Python Dependencies:**
- `fastapi` - Webhook receiver endpoint
- `uvicorn` - ASGI server
- `redis` - Job queue
- `celery` - Background task processing
- `httpx` - Async HTTP calls to Offorte/Airtable
- `pyairtable==2.2.0` - Airtable Python client
- `pydantic` - Data validation
- `pydantic-settings` - Environment configuration
- `python-dotenv` - .env file loading
- `pyyaml` - Configuration file parsing

## SYSTEM PROMPT(S)

```
You are an integration automation agent that syncs accepted proposals from Offorte to Airtable operations systems.

Your responsibilities:
- Process webhook events from Offorte within 5 seconds
- Fetch complete proposal data including all line items and customer details
- Transform Dutch construction quotes to Airtable operational schemas
- Create records across 6 interconnected tables with proper relationships
- Calculate Dutch construction payment splits (30% vooraf, 65% bij start, 5% oplevering)
- Handle errors gracefully with retry logic and detailed logging

Data handling rules:
- Parse "Merk" blocks to identify individual construction elements
- Treat coupled variants (D1, D2) as separate records with shared element_group_id
- Handle Dutch special characters (ë, ï, ö, ü) and € formatting (1.234,56)
- Calculate 18 minutes per element for measurement planning
- Preserve Offorte proposal IDs for reference and idempotency
- Use upsert logic to prevent duplicate records on re-sync

Error handling:
- Retry failed API calls 3 times with exponential backoff (2s, 4s, 8s)
- Queue failed syncs for manual review after retries exhausted
- Log all operations with correlation IDs for debugging
- Never lose data - implement idempotent operations throughout
```

## EXAMPLES:

**Existing codebase patterns to reference:**
- `PRPs/examples/main_agent_reference/` - Settings, providers, tool structure
- `PRPs/examples/tool_enabled_agent/` - External API integration patterns
- `PRPs/examples/testing_examples/` - TestModel and FunctionModel validation

**External patterns to research:**
- FastAPI webhook receivers with Redis queueing
- Celery background worker patterns
- pyairtable batch operations and upsert logic
- Dutch construction business terminology parsing

## DOCUMENTATION:

**Pydantic AI (REQUIRED):**
- https://ai.pydantic.dev/ - Main documentation
- https://ai.pydantic.dev/agents/ - Agent creation patterns
- https://ai.pydantic.dev/tools/ - Tool integration with RunContext
- https://ai.pydantic.dev/testing/ - TestModel/FunctionModel testing
- https://ai.pydantic.dev/models/ - Model provider configuration

**External APIs:**
- https://www.offorte.com/api-docs - Offorte API v2 documentation
- https://airtable.com/developers/web/api/introduction - Airtable API reference
- https://pyairtable.readthedocs.io/ - pyairtable Python client docs

**Background Processing:**
- https://fastapi.tiangolo.com/tutorial/background-tasks/ - FastAPI background tasks
- https://testdriven.io/blog/fastapi-and-celery/ - FastAPI + Celery + Redis pattern
- https://docs.celeryq.dev/ - Celery task queue documentation

## OTHER CONSIDERATIONS:

**Critical Implementation Requirements:**

1. **Webhook Response Time**
   - MUST respond within 5 seconds (Offorte timeout)
   - Queue immediately to Redis, process asynchronously
   - Never execute API calls or data processing in webhook endpoint

2. **Rate Limiting**
   - Offorte: 2 requests/second, 360/hour - implement throttling
   - Airtable: 5 requests/second per base - use batch operations (10 records max)

3. **Data Integrity**
   - Use Offorte `proposal_id` as unique key for idempotency
   - Implement upsert logic to handle re-sync without duplicates
   - Maintain referential integrity across 6 Airtable tables

4. **Dutch Language Handling**
   - Currency format: €1.234,56 (period for thousands, comma for decimal)
   - Special characters: ë, ï, ö, ü must be preserved correctly
   - Date format: DD-MM-YYYY

5. **Coupled Elements Logic**
   - "D1. D2" in proposal means two separate door variants
   - Create separate Airtable records for each
   - Mark as coupled with shared `element_group_id`

6. **Airtable Table Relationships**
   - `klantenportaal` (customers) - customer/contact info
   - `projecten` (projects) - overall project admin
   - `elementen_review` (elements) - individual construction elements
   - `deur_specificaties` (door specs) - door-specific details
   - `facturatie` (invoicing) - 3 invoice records per project
   - `inmeetplanning` (measurement planning) - scheduling with 18 min/element

7. **Security**
   - Validate webhook signatures before processing
   - Store ALL API keys in environment variables via .env
   - Use python-dotenv with pydantic-settings (follow main_agent_reference pattern)
   - Never log sensitive data (API keys, customer details)
   - HTTPS only for all API communication

8. **Testing Strategy**
   - Use TestModel for agent logic validation during development
   - Mock external API calls (Offorte, Airtable) in unit tests
   - Test webhook validation and signature verification
   - Test data transformation with real Dutch proposal examples
   - Integration tests with Airtable sandbox base

9. **Monitoring & Observability**
   - Log all sync operations with unique correlation IDs
   - Track success/failure rates for each table
   - Alert on > 5 failures per hour
   - Dashboard for sync status and queue depth

10. **Agent Architecture**
    - Follow main_agent_reference pattern for settings and providers
    - Default to string output (no result_type unless validation needed)
    - Use @agent.tool with RunContext[SyncAgentDependencies]
    - Keep tools focused and testable independently
    - Implement proper async/await patterns throughout

11. **Scalability & Extensibility (CRITICAL)**
    - **Configuration-driven design**: Store table mappings in YAML/JSON, not hardcoded
    - **Plugin architecture**: Support custom transformation functions (register via config)
    - **Dynamic table discovery**: Load table configs at runtime from config directory
    - **Versioned mappings**: Support multiple mapping versions for API changes
    - **Field extraction registry**: Configure which Offorte fields to extract per table
    - **Adding new tables**:
      1. Create new mapping config file
      2. Define field mappings and transformations
      3. No code changes required - agent loads configs dynamically
    - **Example future additions**:
      - `leveranciers` table → just add `leveranciers.yaml` mapping config
      - Extract proposal attachments → add to `fetch_proposal_data` include_fields
      - New invoice calculation → register custom function in config
