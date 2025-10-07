# Tools Specification for Offorte-Airtable Sync Agent

## Overview

This document specifies the 6 essential tools for the Offorte-to-Airtable sync agent. These tools follow a minimal, single-purpose design philosophy with clear responsibilities and simple error handling.

## Tool Architecture

```
validate_webhook → fetch_proposal_data → parse_construction_elements
                                       ↓
                         transform_proposal_to_table_records
                                       ↓
                              sync_to_airtable
                                       ↑
                    process_won_proposal (orchestrator)
```

---

## Tool 1: validate_webhook

**Purpose**: Validate Offorte webhook signatures for security

**Type**: `@agent.tool_plain` (no external dependencies needed)

**Parameters**:
- `payload: dict` - The webhook payload from Offorte
- `signature: str` - The signature header from request
- `secret: str` - Webhook secret from environment

**Returns**: `Dict[str, Any]`
```python
{
    "valid": True,
    "event_type": "proposal_won",
    "proposal_id": 12345,
    "timestamp": "2025-01-15 14:30:00"
}
```

**Error Handling**:
- Invalid signature: Return `{"valid": False, "error": "Invalid signature"}`
- Missing fields: Return `{"valid": False, "error": "Missing required fields"}`
- No exceptions raised - always return dict

**Implementation Notes**:
- Use HMAC-SHA256 for signature validation
- Extract proposal_id from payload["data"]["id"]
- Support event types: "proposal_won", "proposal_details_updated"
- Must complete in < 100ms (webhook timeout constraint)

---

## Tool 2: fetch_proposal_data

**Purpose**: Fetch complete proposal data from Offorte API

**Type**: `@agent.tool` (needs API key from context)

**Parameters**:
- `ctx: RunContext[AgentDependencies]` - Agent context with API credentials
- `proposal_id: int` - The Offorte proposal ID
- `include_content: bool = True` - Whether to fetch detailed content

**Returns**: `Dict[str, Any]`
```python
{
    "id": 12345,
    "proposal_nr": "2025001NL",
    "name": "Renovatie woning Jansen",
    "status": "won",
    "total_price": 45000.00,
    "company": {
        "name": "Bouwbedrijf Jansen",
        "street": "Hoofdstraat 123",
        "zipcode": "1234 AB",
        "city": "Amsterdam",
        "email": "info@jansen.nl",
        "phone": "+31612345678"
    },
    "contacts": [
        {"id": 234, "name": "Jan Jansen", "email": "jan@jansen.nl"}
    ],
    "content": {
        "blocks": [...]  # If include_content=True
    },
    "custom_fields": {
        "project_date": "2025-02-15",
        "measurement_date": "2025-02-01"
    }
}
```

**Error Handling**:
- API errors: Retry 3 times with exponential backoff (2s, 4s, 8s)
- Rate limit (30 req/min): Wait and retry with proper delay
- Not found: Return `{"error": "Proposal not found", "proposal_id": id}`
- Timeout: Return `{"error": "API timeout", "proposal_id": id}`

**Implementation Notes**:
- Base URL from ctx.deps.offorte_base_url
- API key in Authorization header
- Rate limiting: Track requests per minute
- Combine data from multiple endpoints:
  - GET /proposals/{id}
  - GET /proposals/{id}/content
  - GET /companies/{company_id}
  - GET /contacts/{contact_id}

---

## Tool 3: parse_construction_elements

**Purpose**: Parse Dutch construction elements from proposal content

**Type**: `@agent.tool_plain` (pure data transformation)

**Parameters**:
- `proposal_content: dict` - The content blocks from proposal
- `proposal_nr: str` - Proposal number for element IDs

**Returns**: `List[Dict[str, Any]]`
```python
[
    {
        "element_id": "2025001NL_1",
        "type": "Draaikiep raam",
        "brand": "Merk 1",
        "location": "Woonkamer voor",
        "width_mm": 1200,
        "height_mm": 2400,
        "coupled": False,
        "variant": None,
        "price": 3500.00,
        "notes": "Wit kunststof, dubbel glas"
    },
    {
        "element_id": "2025001NL_2",
        "type": "Voordeur",
        "brand": "Merk 2",
        "location": "Entree",
        "width_mm": 1000,
        "height_mm": 2300,
        "coupled": True,
        "variant": "D1",
        "price": 4200.00,
        "notes": "Antraciet, veiligheidsslot"
    }
]
```

**Error Handling**:
- Invalid content structure: Return empty list `[]`
- Missing dimensions: Set to None, don't fail
- Unparseable price: Set to 0.00
- Log warnings for unrecognized patterns

**Implementation Notes**:
- Identify "Merk blocks" using regex: `Merk \d+:`
- Extract element types: Draaikiep, Vast raam, Voordeur, etc.
- Parse dimensions: `1200x2400mm` format
- Detect coupled elements: "D1. D2. D3" patterns
- Handle Dutch special characters: ë, ï, ö, ü
- Element numbering: sequential within proposal

**Parsing Patterns**:
```python
ELEMENT_TYPES = [
    "Draaikiep raam",
    "Vast raam",
    "Voordeur",
    "Achterdeur",
    "Schuifpui"
]

DIMENSION_PATTERN = r"(\d+)\s*x\s*(\d+)\s*mm"
COUPLED_PATTERN = r"D(\d+)\."
BRAND_PATTERN = r"Merk\s+(\d+):"
```

---

## Tool 4: transform_proposal_to_table_records

**Purpose**: Transform Offorte data to Airtable table schemas

**Type**: `@agent.tool_plain` (pure transformation logic)

**Parameters**:
- `proposal: dict` - Complete proposal data
- `elements: List[dict]` - Parsed construction elements

**Returns**: `Dict[str, List[Dict]]`
```python
{
    "klantenportaal": [{...}],      # 1 customer record
    "projecten": [{...}],            # 1 project record
    "elementen_review": [{...}, ...],# N element records
    "inmeetplanning": [{...}],       # 1 planning record
    "facturatie": [{...}, {...}, {...}],  # 3 invoice records
    "deur_specificaties": [{...}, ...]    # M door records
}
```

**Error Handling**:
- Missing required fields: Use sensible defaults, log warnings
- Invalid data types: Convert with fallbacks
- Empty elements list: Still create customer/project records
- Never raise exceptions - always return dict with partial data

**Implementation Notes**:

### Customer Portal Record (klantenportaal)
```python
{
    "Bedrijfsnaam": proposal["company"]["name"],
    "Adres": proposal["company"]["street"],
    "Postcode": proposal["company"]["zipcode"],
    "Plaats": proposal["company"]["city"],
    "Email": proposal["company"]["email"],
    "Telefoon": proposal["company"]["phone"],
    "Contact Persoon": proposal["contacts"][0]["name"],
    "Offerte Nummer": proposal["proposal_nr"],
    "Status": "Actief"
}
```

### Project Record (projecten)
```python
{
    "Project Nummer": proposal["proposal_nr"],
    "Naam": proposal["name"],
    "Klant": proposal["company"]["name"],
    "Totaal Bedrag": proposal["total_price"],
    "Start Datum": proposal["custom_fields"]["project_date"],
    "Eind Datum": add_days(proposal["custom_fields"]["project_date"], 60),
    "Status": "Gewonnen",
    "Verantwoordelijke": proposal.get("account_user_name", ""),
    "Offorte ID": proposal["id"]
}
```

### Element Review Records (elementen_review)
```python
# For each element:
{
    "Order Nummer": proposal["proposal_nr"],
    "Element ID": element["element_id"],
    "Type": element["type"],
    "Merk": element["brand"],
    "Locatie": element["location"],
    "Breedte (mm)": element["width_mm"],
    "Hoogte (mm)": element["height_mm"],
    "Gekoppeld": element["coupled"],
    "Variant": element["variant"],
    "Prijs": element["price"],
    "Opmerkingen": element["notes"]
}
```

### Measurement Planning Record (inmeetplanning)
```python
{
    "Order Nummer": proposal["proposal_nr"],
    "Klant": proposal["company"]["name"],
    "Aantal Elementen": len(elements),
    "Geschatte Tijd (min)": len(elements) * 18,  # 18 min per element
    "Geplande Datum": proposal["custom_fields"]["measurement_date"],
    "Status": "Te plannen",
    "Toegewezen aan": None
}
```

### Invoice Records (facturatie) - 3 splits
```python
[
    {
        "Order Nummer": proposal["proposal_nr"],
        "Factuur Type": "30% - Vooraf",
        "Bedrag": proposal["total_price"] * 0.30,
        "Datum": today(),
        "Status": "Concept"
    },
    {
        "Order Nummer": proposal["proposal_nr"],
        "Factuur Type": "65% - Start",
        "Bedrag": proposal["total_price"] * 0.65,
        "Datum": proposal["custom_fields"]["project_date"],
        "Status": "Gepland"
    },
    {
        "Order Nummer": proposal["proposal_nr"],
        "Factuur Type": "5% - Oplevering",
        "Bedrag": proposal["total_price"] * 0.05,
        "Datum": add_days(proposal["custom_fields"]["project_date"], 60),
        "Status": "Gepland"
    }
]
```

### Door Specifications (deur_specificaties)
```python
# Only for door elements (type contains "deur"):
{
    "Order Nummer": proposal["proposal_nr"],
    "Deur Type": element["type"],
    "Model": extract_model(element["notes"]),
    "Kleur": extract_color(element["notes"]),
    "Glastype": extract_glass(element["notes"]),
    "Sluitwerk": extract_locks(element["notes"]),
    "Speciale Kenmerken": element["notes"]
}
```

**Helper Functions**:
- `add_days(date_str, days)` - Add days to DD-MM-YYYY format
- `today()` - Current date in DD-MM-YYYY format
- `extract_*()` - Parse specific attributes from notes field

---

## Tool 5: sync_to_airtable

**Purpose**: Create/update records in Airtable with batch operations

**Type**: `@agent.tool` (needs Airtable API key from context)

**Parameters**:
- `ctx: RunContext[AgentDependencies]` - Agent context with Airtable credentials
- `base_id: str` - Airtable base ID
- `table_name: str` - Table name within base
- `records: List[dict]` - Records to sync
- `key_field: str = "Order Nummer"` - Field to check for duplicates

**Returns**: `Dict[str, Any]`
```python
{
    "success": True,
    "created": 5,
    "updated": 2,
    "failed": 0,
    "record_ids": ["rec123", "rec456", ...],
    "errors": []
}
```

**Error Handling**:
- Rate limit (5 req/sec): Implement automatic throttling
- Validation errors: Collect in errors list, continue with valid records
- Network errors: Retry 3 times with exponential backoff
- Partial success: Return what succeeded + error details

**Implementation Notes**:
- Batch size: Maximum 10 records per API call
- Upsert logic: If key_field provided, check for existing records first
- Rate limiting: Track requests per second, wait if needed
- Field validation: Ensure field names match Airtable schema
- Use pyairtable library for API interaction

**Batch Processing**:
```python
# Process in chunks of 10
for chunk in chunks(records, 10):
    # Check existing records by key_field
    existing = await fetch_existing(key_field_values)

    # Separate creates vs updates
    to_create = [r for r in chunk if not exists]
    to_update = [r for r in chunk if exists]

    # Execute batch operations
    created_ids = await batch_create(to_create)
    updated_ids = await batch_update(to_update)

    # Wait for rate limit (5 req/sec)
    await asyncio.sleep(0.21)
```

**Airtable API Configuration**:
- Base URL: `https://api.airtable.com/v0/{base_id}/{table_name}`
- Headers: `Authorization: Bearer {api_key}`
- Create: POST with `{"records": [{"fields": {...}}, ...]}`
- Update: PATCH with `{"records": [{"id": "rec123", "fields": {...}}, ...]}`

---

## Tool 6: process_won_proposal

**Purpose**: End-to-end orchestration of proposal sync

**Type**: `@agent.tool` (orchestrates other tools)

**Parameters**:
- `ctx: RunContext[AgentDependencies]` - Agent context
- `proposal_id: int` - Offorte proposal ID

**Returns**: `Dict[str, Any]`
```python
{
    "success": True,
    "proposal_id": 12345,
    "proposal_nr": "2025001NL",
    "sync_summary": {
        "klantenportaal": {"created": 1, "updated": 0},
        "projecten": {"created": 1, "updated": 0},
        "elementen_review": {"created": 8, "updated": 0},
        "inmeetplanning": {"created": 1, "updated": 0},
        "facturatie": {"created": 3, "updated": 0},
        "deur_specificaties": {"created": 2, "updated": 0}
    },
    "total_records_created": 16,
    "processing_time_seconds": 4.2,
    "errors": []
}
```

**Error Handling**:
- Continue on partial failures - sync what's possible
- Collect all errors in errors list
- Mark success=False only if critical failure (no data synced)
- Log correlation ID for debugging

**Implementation Notes**:

### Orchestration Steps:
```python
async def process_won_proposal(ctx, proposal_id):
    correlation_id = generate_uuid()
    logger.info(f"Starting sync {correlation_id} for proposal {proposal_id}")

    try:
        # Step 1: Fetch proposal data
        proposal = await fetch_proposal_data(ctx, proposal_id, include_content=True)
        if "error" in proposal:
            return {"success": False, "error": proposal["error"]}

        # Step 2: Parse construction elements
        elements = parse_construction_elements(
            proposal["content"],
            proposal["proposal_nr"]
        )

        # Step 3: Transform to table records
        table_records = transform_proposal_to_table_records(proposal, elements)

        # Step 4: Sync to all 6 Airtable tables
        sync_summary = {}
        errors = []

        for table_name, records in table_records.items():
            base_id = get_base_id_for_table(ctx.deps, table_name)

            result = await sync_to_airtable(
                ctx,
                base_id,
                table_name,
                records,
                key_field="Order Nummer"
            )

            sync_summary[table_name] = {
                "created": result["created"],
                "updated": result["updated"]
            }

            if result["failed"] > 0:
                errors.extend(result["errors"])

        # Step 5: Calculate totals
        total_created = sum(s["created"] for s in sync_summary.values())

        return {
            "success": len(errors) == 0,
            "proposal_id": proposal_id,
            "proposal_nr": proposal["proposal_nr"],
            "sync_summary": sync_summary,
            "total_records_created": total_created,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Critical failure in sync {correlation_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "correlation_id": correlation_id
        }
```

**Base ID Mapping**:
```python
def get_base_id_for_table(deps, table_name):
    mapping = {
        "klantenportaal": deps.airtable_base_administration,
        "projecten": deps.airtable_base_administration,
        "facturatie": deps.airtable_base_administration,
        "elementen_review": deps.airtable_base_sales_review,
        "inmeetplanning": deps.airtable_base_technisch,
        "deur_specificaties": deps.airtable_base_technisch
    }
    return mapping.get(table_name)
```

---

## Dependencies Configuration

**AgentDependencies Model**:
```python
@dataclass
class AgentDependencies:
    # Offorte API
    offorte_api_key: str
    offorte_account_name: str
    offorte_base_url: str  # Computed: f"https://connect.offorte.com/api/v2/{account_name}/"

    # Airtable API
    airtable_api_key: str
    airtable_base_administration: str
    airtable_base_sales_review: str
    airtable_base_technisch: str

    # Webhook security
    webhook_secret: str

    # Optional: Redis for queueing
    redis_url: str = "redis://localhost:6379"
```

**Settings Loading**:
```python
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    # Offorte
    offorte_api_key: str
    offorte_account_name: str

    # Airtable
    airtable_api_key: str
    airtable_base_administration: str
    airtable_base_sales_review: str
    airtable_base_technisch: str

    # Security
    webhook_secret: str

    # Optional
    redis_url: str = "redis://localhost:6379"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

def load_settings() -> Settings:
    load_dotenv()
    return Settings()
```

---

## Testing Strategy

### Unit Tests for Each Tool:

**test_validate_webhook.py**:
```python
def test_valid_signature():
    payload = {"type": "proposal_won", "data": {"id": 123}}
    signature = generate_hmac(payload, "secret")
    result = validate_webhook(payload, signature, "secret")
    assert result["valid"] is True

def test_invalid_signature():
    payload = {"type": "proposal_won", "data": {"id": 123}}
    result = validate_webhook(payload, "wrong_sig", "secret")
    assert result["valid"] is False
```

**test_fetch_proposal.py**:
```python
@pytest.mark.asyncio
async def test_fetch_proposal_success(mock_httpx):
    mock_httpx.get.return_value.json.return_value = {...}
    result = await fetch_proposal_data(ctx, 12345)
    assert result["id"] == 12345

@pytest.mark.asyncio
async def test_fetch_proposal_retry_on_rate_limit(mock_httpx):
    # Test exponential backoff
    pass
```

**test_parse_elements.py**:
```python
def test_parse_coupled_doors():
    content = {...}  # Dutch proposal with "D1. D2."
    elements = parse_construction_elements(content, "2025001NL")
    assert len(elements) == 2
    assert elements[0]["coupled"] is True
    assert elements[0]["variant"] == "D1"

def test_parse_dimensions():
    content = {...}  # "1200x2400mm"
    elements = parse_construction_elements(content, "2025001NL")
    assert elements[0]["width_mm"] == 1200
    assert elements[0]["height_mm"] == 2400
```

**test_transform.py**:
```python
def test_invoice_splits():
    proposal = {"total_price": 45000.00, ...}
    records = transform_proposal_to_table_records(proposal, [])
    invoices = records["facturatie"]
    assert len(invoices) == 3
    assert invoices[0]["Bedrag"] == 13500.00  # 30%
    assert invoices[1]["Bedrag"] == 29250.00  # 65%
    assert invoices[2]["Bedrag"] == 2250.00   # 5%
```

**test_airtable_sync.py**:
```python
@pytest.mark.asyncio
async def test_batch_create(mock_airtable):
    records = [{"fields": {...}} for _ in range(15)]
    result = await sync_to_airtable(ctx, "appXXX", "table", records)
    assert result["created"] == 15
    assert mock_airtable.batch_create.call_count == 2  # 10 + 5

@pytest.mark.asyncio
async def test_upsert_logic(mock_airtable):
    # Test update existing vs create new
    pass
```

---

## Error Handling Summary

| Tool | Error Type | Strategy |
|------|-----------|----------|
| validate_webhook | Invalid signature | Return `{"valid": False}` |
| fetch_proposal_data | API timeout | Retry 3x exponential backoff |
| fetch_proposal_data | Rate limit | Wait and retry with delay |
| parse_construction_elements | Bad format | Return empty list, log warning |
| transform_proposal_to_table_records | Missing fields | Use defaults, log warning |
| sync_to_airtable | Rate limit | Auto-throttle to 5 req/sec |
| sync_to_airtable | Validation error | Continue with valid records |
| process_won_proposal | Partial failure | Continue, collect errors |

---

## Performance Requirements

| Tool | Max Time | Notes |
|------|----------|-------|
| validate_webhook | 100ms | Webhook timeout constraint |
| fetch_proposal_data | 3s | Network + API processing |
| parse_construction_elements | 500ms | Pure computation |
| transform_proposal_to_table_records | 200ms | Pure computation |
| sync_to_airtable | 5s | Rate limiting + network |
| process_won_proposal | 15s | End-to-end orchestration |

---

## Rate Limiting Implementation

**Offorte (30 req/min)**:
```python
class OfforteLimiter:
    def __init__(self):
        self.requests = []

    async def wait_if_needed(self):
        now = time.time()
        # Remove requests older than 60 seconds
        self.requests = [r for r in self.requests if now - r < 60]

        if len(self.requests) >= 30:
            # Wait until oldest request is 60 seconds old
            wait_time = 60 - (now - self.requests[0])
            await asyncio.sleep(wait_time)

        self.requests.append(now)
```

**Airtable (5 req/sec)**:
```python
class AirtableLimiter:
    def __init__(self):
        self.last_request = 0

    async def wait_if_needed(self):
        now = time.time()
        time_since_last = now - self.last_request

        if time_since_last < 0.2:  # 5 req/sec = 0.2s between
            await asyncio.sleep(0.2 - time_since_last)

        self.last_request = time.time()
```

---

## Security Considerations

1. **Webhook Signature Validation**:
   - Use HMAC-SHA256 with shared secret
   - Compare signatures with constant-time algorithm
   - Reject unsigned webhooks

2. **API Key Management**:
   - Never log API keys
   - Load from environment variables only
   - Use different keys for dev/prod

3. **Input Sanitization**:
   - Validate all numeric IDs
   - Sanitize string inputs before database writes
   - Prevent SQL/NoSQL injection

4. **Rate Limiting**:
   - Implement per-tool rate limiting
   - Prevent DoS via webhook spam
   - Use Redis for distributed rate limiting

---

## Monitoring & Logging

**Log Levels**:
- INFO: Successful operations, sync summaries
- WARNING: Retries, missing optional fields
- ERROR: API failures, validation errors
- CRITICAL: Data loss risks, security violations

**Key Metrics**:
- Webhook processing time (< 1s target)
- API success rate (> 99% target)
- Sync completion time (< 15s target)
- Records synced per hour
- Error rate by type

**Correlation IDs**:
- Generate UUID for each proposal sync
- Include in all log messages
- Return in sync results for debugging

---

## Implementation Checklist

- [ ] Tool 1: validate_webhook with HMAC-SHA256
- [ ] Tool 2: fetch_proposal_data with retry logic
- [ ] Tool 3: parse_construction_elements with Dutch patterns
- [ ] Tool 4: transform_proposal_to_table_records with 6 schemas
- [ ] Tool 5: sync_to_airtable with batch + upsert
- [ ] Tool 6: process_won_proposal orchestration
- [ ] Rate limiters for Offorte and Airtable
- [ ] Unit tests for all tools
- [ ] Integration tests with TestModel
- [ ] Error handling and logging
- [ ] Security: webhook validation, API key management
- [ ] Monitoring: correlation IDs, metrics logging

---

## Next Steps

1. **Main Agent Integration**: Use these tool specifications to create the Pydantic AI agent
2. **Dependencies Setup**: Implement AgentDependencies and Settings classes
3. **FastAPI Wrapper**: Create webhook receiver endpoint
4. **Background Worker**: Implement Celery/Redis queue processing
5. **Testing**: Comprehensive unit and integration tests
6. **Deployment**: Docker container with monitoring

This specification provides the foundation for a minimal, production-ready sync agent that follows Pydantic AI best practices.
