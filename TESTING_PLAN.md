# Realistic Testing Plan

## Current Status: ⚠️ NOT READY FOR PRODUCTION

The code is **architecturally sound** but **untested** with real data. Here's what needs to happen:

---

## Phase 1: Basic Setup (15 minutes)

### 1. Install Dependencies
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

**Expected Issues**:
- `pydantic-ai` version might not exist or API different
- Version conflicts

**Fix**: Adjust versions in requirements.txt

### 2. Test Basic Imports
```bash
# Test if code can import
python -c "from backend.core.settings import Settings; print('✅ Imports work')"
```

**If this fails**: Imports are broken, need to fix paths

---

## Phase 2: Settings & Config (10 minutes)

### 1. Create .env File
```bash
cp .env.example .env
# Edit .env with FAKE test credentials first
```

### 2. Test Settings Load
```bash
python -c "
from backend.core.settings import load_settings
try:
    settings = load_settings()
    print('✅ Settings loaded')
except Exception as e:
    print(f'❌ Settings failed: {e}')
"
```

**If this fails**: Environment variable issues

---

## Phase 3: Test Without Real APIs (30 minutes)

### 1. Unit Tests (No API calls)
```bash
# Run unit tests that don't need real APIs
pytest tests/unit/ -v
```

**Expected**: Some tests will fail due to:
- Pydantic AI API differences
- Import issues
- Mock setup problems

### 2. Fix Obvious Errors
- Update Pydantic AI imports if needed
- Fix any Python syntax errors
- Adjust mocks

---

## Phase 4: Get Real Data Samples (CRITICAL!)

**You MUST do this before testing with real webhook**:

### 1. Get Offorte Webhook Payload
```bash
# In Offorte, trigger a test webhook or look at webhook logs
# Save actual payload to: tests/fixtures/real_offorte_payload.json
```

**Example payload you need**:
```json
{
  "type": "proposal_won",
  "date_created": "2025-01-15 14:30:00",
  "data": {
    "id": 12345,
    "proposal_nr": "2025001NL",
    ...
  }
}
```

### 2. Get Offorte API Response
```bash
# Make actual API call to Offorte
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://connect.offorte.com/api/v2/YOUR_ACCOUNT/proposals/12345

# Save to: tests/fixtures/real_offorte_proposal.json
```

### 3. Check Airtable Schema
```bash
# In Airtable, check ACTUAL field names for each table
# Example: Is it "Bedrijfsnaam" or "Company Name"?
# Document in: config/airtable_actual_fields.yaml
```

---

## Phase 5: Test with Real API (Carefully!)

### 1. Test Settings with Real Keys
```bash
# Put ONE real API key in .env
LLM_API_KEY=sk-real-key-here

# Test it works
python -c "
from backend.core.providers import get_llm_model
model = get_llm_model()
print('✅ LLM provider works')
"
```

### 2. Test Offorte API (Read-only!)
```bash
# Test fetching ONE proposal (no writes!)
python examples/simple_sync.py
```

**This will likely FAIL at**:
- API authentication
- Field parsing
- Data transformation

### 3. Fix Issues One by One
- Update `backend/agent/tools.py` with correct API calls
- Fix field mappings
- Adjust parsing logic

---

## Phase 6: Dry Run Test (No Airtable Writes!)

### 1. Comment Out Airtable Writes
In `backend/agent/tools.py`, modify `sync_to_airtable`:
```python
async def sync_to_airtable(...):
    # TESTING: Don't actually write
    print(f"Would sync to {table_name}: {records}")
    return SyncResult(
        table_name=table_name,
        created=len(records),
        updated=0,
        failed=0
    )
```

### 2. Run Full Pipeline
```bash
python -c "
import asyncio
from backend.agent.agent import process_proposal_sync

async def test():
    result = await process_proposal_sync(
        proposal_id=12345,  # Real proposal ID
        job_id='test-run'
    )
    print(result)

asyncio.run(test())
"
```

**Expected output**:
- Should fetch proposal
- Should parse elements
- Should print what WOULD be written

---

## Phase 7: Single Table Test

### 1. Test ONE Table Only
```bash
# Modify code to only sync to ONE test table
# Create a test table in Airtable with few records
# Try syncing just that
```

### 2. Verify Data
- Check Airtable manually
- Verify all fields correct
- Check for duplicates

---

## Phase 8: Full Integration Test

Only after ALL above passes:

### 1. Test with Webhook
```bash
# Start Redis
redis-server

# Start FastAPI
uvicorn backend.api.server:app --reload

# Use Postman/curl to send test webhook
curl -X POST http://localhost:8000/webhook/offorte \
  -H "Content-Type: application/json" \
  -H "X-Offorte-Signature: test-sig" \
  -d @tests/fixtures/real_offorte_payload.json
```

### 2. Monitor Logs
```bash
tail -f logs/sync_*.log
```

---

## What Will DEFINITELY Need Fixing

### 1. Offorte API Integration
**File**: `backend/agent/tools.py` - `fetch_proposal_data()`

**Issues**:
- API endpoint URLs might be wrong
- Response structure unknown
- Field names guessed

**Fix**: Use real API docs and test responses

### 2. Dutch Parsing
**File**: `backend/agent/tools.py` - `parse_construction_elements()`

**Issues**:
- Regex patterns are guesses
- "Merk" block structure unknown
- Coupled elements pattern might be wrong

**Fix**: Get real Dutch proposal examples

### 3. Airtable Field Names
**File**: `backend/agent/tools.py` - `_transform_*()` functions

**Issues**:
- Field names are complete guesses
- Don't know if they're in Dutch or English
- Field types might be wrong

**Fix**: Check actual Airtable schema

### 4. Invoice Calculation
**File**: `backend/agent/tools.py` - `_transform_invoices()`

**Issues**:
- Date calculations might be wrong
- Don't know where project dates come from

**Fix**: Verify with real proposal data

---

## Minimum Viable Test

**Before accepting a real proposal**, do this:

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Add ONLY test credentials to .env
# 3. Run this:
python -c "
from backend.core.settings import load_settings
from backend.agent.tools import validate_webhook

settings = load_settings()
print('✅ Settings work')

result = validate_webhook(
    {'type': 'proposal_won', 'data': {'id': 123}},
    'test-sig',
    'test-secret'
)
print(f'✅ Webhook validation: {result}')
"
```

If this works → confidence level goes from 30% to 50%

Then test each tool one by one.

---

## Realistic Timeline

- **Install & basic tests**: 1-2 hours
- **Get real data samples**: 2-4 hours
- **Fix Offorte integration**: 2-3 hours
- **Fix Airtable integration**: 1-2 hours
- **Test full pipeline**: 1-2 hours
- **Debug issues**: 2-4 hours

**Total**: 10-20 hours of actual testing/fixing

---

## My Recommendation

**DON'T wait for a real proposal!**

Instead:

1. **Install deps now** (5 min)
2. **Test basic imports** (5 min)
3. **Get Offorte API sample** (1 hour)
4. **Test one tool at a time** (2 hours)
5. **Fix issues incrementally** (ongoing)

**When you get a real proposal**: You'll be 80% ready instead of 30% ready.

---

## Bottom Line

**Current state**: Solid architecture, untested code
**Confidence without testing**: 30-40%
**Confidence after testing plan**: 70-80%

**Best approach**: Test incrementally NOW, don't wait for production.
