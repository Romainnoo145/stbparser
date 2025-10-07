# Offorte-to-Airtable Sync Agent

Automated Pydantic AI agent that syncs accepted proposals from Offorte to multiple Airtable bases for operations management.

## Overview

This agent listens for Offorte webhook events (proposal_won), fetches complete proposal data, transforms Dutch construction quotes, and creates records across 6 operational Airtable tables.

**Business Value**:
- Eliminates 30+ minutes of manual data entry per accepted proposal
- Zero data entry errors through automated validation
- Instant visibility of won proposals in operations systems
- Automatic invoice scheduling (30/65/5 payment splits)

## Architecture

```
Offorte Proposal Won
  ↓
FastAPI Webhook Receiver (< 5 sec response)
  ↓
Redis Queue
  ↓
Celery Background Worker
  ↓
Pydantic AI Agent
  ├── Fetch Proposal Data (Offorte API)
  ├── Parse Construction Elements (Dutch parsing)
  ├── Transform to Airtable Schemas
  └── Sync to 6 Airtable Tables
```

## Features

### Core Capabilities
- **Webhook Processing**: Validates and queues Offorte events instantly (< 1 sec)
- **Data Fetching**: Retrieves complete proposal data with retry logic
- **Dutch Parsing**: Handles Dutch construction terminology, special characters (€, ë, ï), and number formatting (1.234,56)
- **Element Detection**: Identifies coupled elements (D1, D2 variants) as separate records
- **Invoice Splitting**: Automatically calculates 30% vooraf, 65% bij start, 5% oplevering
- **Batch Operations**: Syncs to Airtable with batch operations (10 records max) and upsert logic

### Airtable Tables Synced
1. **klantenportaal** (Customer Portal) - Customer and contact information
2. **projecten** (Projects) - Overall project administration
3. **elementen_review** (Elements) - Individual construction element specifications
4. **inmeetplanning** (Measurement Planning) - Scheduling with 18 min/element calculation
5. **facturatie** (Invoicing) - 3 invoice records with payment splits
6. **deur_specificaties** (Door Specs) - Door-specific technical details

## Installation

### Prerequisites
- Python 3.10+
- Redis server
- Offorte API credentials
- Airtable API key and base IDs
- OpenAI API key

### Setup

1. **Clone and navigate to directory**:
```bash
cd offorte_airtable_sync
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

Required environment variables:
- `OFFORTE_API_KEY` - Your Offorte API key
- `OFFORTE_ACCOUNT_NAME` - Your Offorte account name
- `AIRTABLE_API_KEY` - Your Airtable API key
- `AIRTABLE_BASE_ADMINISTRATION` - Administration base ID
- `AIRTABLE_BASE_SALES_REVIEW` - Sales review base ID
- `AIRTABLE_BASE_TECHNISCH` - Technical base ID
- `LLM_API_KEY` - OpenAI API key
- `WEBHOOK_SECRET` - Secret for webhook signature validation
- `REDIS_URL` - Redis connection URL

## Usage

### Start the Services

1. **Start Redis** (if not already running):
```bash
redis-server
```

2. **Start FastAPI webhook server**:
```bash
python -m uvicorn offorte_airtable_sync.server:app --host 0.0.0.0 --port 8000
```

3. **Start Celery worker** (in separate terminal):
```bash
celery -A offorte_airtable_sync.worker worker --loglevel=info
```

### Configure Offorte Webhook

1. Go to Offorte Settings → Webhooks
2. Add new webhook:
   - URL: `https://your-domain.com/webhook/offorte`
   - Events: `proposal_won`
   - Secret: Use the same value as `WEBHOOK_SECRET` in .env

### API Endpoints

#### Health Check
```bash
GET /
GET /health
```

#### Webhook Receiver
```bash
POST /webhook/offorte
Headers:
  X-Offorte-Signature: <hmac-sha256-signature>
Body:
  {
    "type": "proposal_won",
    "date_created": "2025-01-15 14:30:00",
    "data": {
      "id": 12345,
      "name": "Offerte 2025001NL",
      ...
    }
  }
```

#### Queue Status
```bash
GET /queue/status
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=offorte_airtable_sync

# Run specific test file
pytest tests/test_tools.py -v
```

### Code Quality

```bash
# Format code
black offorte_airtable_sync/

# Lint code
ruff check offorte_airtable_sync/

# Type checking (if mypy configured)
mypy offorte_airtable_sync/
```

### Direct Agent Usage (for testing)

```python
import asyncio
from offorte_airtable_sync import process_proposal_sync

async def test_sync():
    result = await process_proposal_sync(
        proposal_id=12345,
        job_id="test-job-123"
    )
    print(result)

asyncio.run(test_sync())
```

## Architecture Details

### Agent Tools

The agent uses 6 essential tools:

1. **validate_webhook**: HMAC-SHA256 signature validation
2. **fetch_proposal_data**: Fetches from Offorte API with retry logic
3. **parse_construction_elements**: Parses Dutch proposal content
4. **transform_proposal_to_table_records**: Maps to Airtable schemas
5. **sync_to_airtable**: Batch operations with upsert logic
6. **process_won_proposal**: End-to-end orchestration

### Error Handling

- **API Failures**: 3 retries with exponential backoff (2s, 4s, 8s)
- **Rate Limiting**: Automatic throttling (Offorte: 30/min, Airtable: 5/sec)
- **Partial Failures**: Continues processing, collects errors
- **Idempotency**: Uses Offorte proposal_id as unique key

### Data Transformations

#### Invoice Splits
```python
Total: €45,000
- 30% Vooraf: €13,500 (immediate)
- 65% Bij Start: €29,250 (project date)
- 5% Oplevering: €2,250 (project date + 60 days)
```

#### Measurement Planning
```
Elements: 8
Estimated Time: 8 × 18 minutes = 144 minutes (2.4 hours)
```

#### Coupled Elements
```
Input: "D1. D2. Voordeur"
Output: 2 separate records with shared element_group_id
```

## Monitoring

### Logs

Logs are written to `logs/sync_{time}.log` with rotation:
- Rotation: Daily
- Retention: 30 days
- Format: `{time} | {level} | {message}`

### Key Metrics

- Webhook response time (target: < 1 second)
- Sync success rate (target: > 99%)
- API call latencies
- Queue depth
- Records synced per hour

### Correlation IDs

Every sync operation generates a unique correlation ID for debugging. Check logs with:
```bash
grep "correlation-id-here" logs/sync_*.log
```

## Troubleshooting

### Webhook Not Receiving Events
1. Check Offorte webhook configuration
2. Verify webhook secret matches
3. Check server logs: `tail -f logs/sync_*.log`
4. Test with curl:
```bash
curl -X POST http://localhost:8000/webhook/offorte \
  -H "Content-Type: application/json" \
  -H "X-Offorte-Signature: test-signature" \
  -d '{"type":"proposal_won","data":{"id":123}}'
```

### Sync Failures
1. Check Celery worker logs
2. Verify API credentials in .env
3. Check Redis connection: `redis-cli ping`
4. Review error messages in sync report

### Rate Limiting Issues
- Offorte: Max 30 requests/minute - agent automatically throttles
- Airtable: Max 5 requests/second - uses batch operations

## Production Deployment

### Environment Variables
```bash
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start server
CMD ["uvicorn", "offorte_airtable_sync.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  worker:
    build: .
    command: celery -A offorte_airtable_sync.worker worker --loglevel=info
    depends_on:
      - redis
```

## Security

- **API Keys**: Stored in environment variables, never logged
- **Webhook Validation**: HMAC-SHA256 signature verification
- **HTTPS Only**: All API communication over HTTPS
- **Input Sanitization**: Validates all data before Airtable writes

## License

Generated by Claude Code

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review correlation IDs for specific syncs
3. Verify environment configuration in `.env`
