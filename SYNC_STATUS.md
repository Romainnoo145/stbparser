# Offorte-to-Airtable Sync System - Status Report

**Last Updated:** 2025-10-08
**Status:** ✅ **FULLY OPERATIONAL** - All 7 tables syncing successfully

---

## System Overview

Automated webhook-based sync system that syncs won Offorte proposals to 7 Airtable tables across 2 bases:
- **STB-SALES** (5 tables) - Customer portal, elements, specs, subproducts, post-calculation
- **STB-ADMINISTRATIE** (2 tables) - Measurement planning, project tracking

---

## Current State: ✅ ALL SYSTEMS OPERATIONAL

### STB-SALES Base (app9mz6mT0zk8XRGm)

| Table | Status | Records (Proposal 299654) | Notes |
|-------|--------|---------------------------|-------|
| **Klantenportaal** | ✅ Working | 1 record | Customer portal entry |
| **Elementen Overzicht** | ✅ Working | 9 records | Element overview |
| **Element Specificaties** | ✅ Working | 9 records | Element specifications |
| **Subproducten** | ✅ Working | 9 records | Sub-products |
| **Nacalculatie** | ✅ Working | 9 records | Post-calculation tracking |

### STB-ADMINISTRATIE Base (appuXCPmvIwowH78k)

| Table | Status | Records (Proposal 299654) | Notes |
|-------|--------|---------------------------|-------|
| **Inmeetplanning** | ✅ Working | 1 record | Status: "Te Plannen" |
| **Projecten** | ✅ Working | 1 record | Status: "Verkocht" |

### Product Catalogus (STB-SALES)

| Table | Status | Total Products | Purpose |
|-------|--------|----------------|---------|
| **Product Catalogus** | ✅ Created | 36 products | Passive catalog for future cost price matching (NOT yet implemented) |

**Product Categories:**
- 6 Glas products (HR++, HR+++, Triple, etc.)
- 5 Hordeur products (Plisse, Insecten, etc.)
- 5 Beslag products (Hang- en sluitwerk, etc.)
- 9 Onderdeel products (Dorpels, Kit, etc.)
- 3 Profiel products (Kunststof, Aluminium, Hout)
- 2 Dakraam products (Keylite, Velux)
- 6 Service/Assembly products

---

## Technical Architecture

### 1. Webhook Flow
```
Offorte (proposal_won)
    ↓
Localtunnel (https://small-terms-cover.loca.lt)
    ↓
FastAPI Server (localhost:8002)
    ↓
Redis Queue (background processing)
    ↓
ProposalSyncService
    ↓
Transform (offorte_to_airtable.py + administratie_transforms.py)
    ↓
AirtableSync (upsert to 7 tables)
```

### 2. Key Components

**Backend Services:**
- `backend/services/proposal_sync.py` - Main orchestrator
- `backend/services/airtable_sync.py` - Airtable CRUD operations
- `backend/api/server.py` - Webhook receiver (FastAPI)
- `backend/workers/proposal_worker.py` - Background job processor

**Transformers:**
- `backend/transformers/offorte_to_airtable.py` - STB-SALES transformations (5 tables)
- `backend/transformers/administratie_transforms.py` - STB-ADMINISTRATIE transformations (2 tables)

**Configuration:**
- `config/airtable_field_mappings.py` - Field schemas and base routing
- `.env` - API keys and settings

### 3. Data Cleaning Pattern

All records are cleaned before syncing using `_clean_record_data()`:
- Removes `None` values
- Removes empty strings (`""`)
- Prevents 422 errors from singleSelect fields

---

## Field Mapping Fixes Applied

### Issue 1: Element Specificaties - Empty singleSelect Values
**Problem:** Empty string `""` sent to "Draairichting" singleSelect field
**Fix:** Filter out empty strings in `_clean_record_data()`
**Result:** ✅ 9/9 records syncing

### Issue 2: Subproducten - Invalid "Standaard" Category
**Problem:** Default value "Standaard" not in allowed options
**Fix:** Changed default from `"Standaard"` to `None`
**Result:** ✅ 9/9 records syncing (actually 45 subproducts total)

### Issue 3: Nacalculatie - Invalid "Te Bepalen" Status
**Problem:** "Te Bepalen" not in "Kostprijs Status" options
**Fix:** Changed default to `None`
**Result:** ✅ 9/9 records syncing

### Issue 4: Inmeetplanning - Wrong Field Type
**Problem:** Sent "9 elementen" (text) to "Elementen" (number field)
**Fix:** Send `num_elements` (int) instead of formatted string
**Result:** ✅ 1/1 records syncing

### Issue 5: Inmeetplanning - Invalid "Nieuw" Status
**Problem:** "Nieuw" not in "Projectstatus" singleSelect options
**Valid Options:** Te Plannen, Gepland, Voltooid, Geannuleerd
**Fix:** Changed to "Te Plannen"
**Result:** ✅ 1/1 records syncing

### Issue 6: Projecten - Invalid "Nieuw" Status
**Problem:** "Nieuw" not in "Project Status" singleSelect options
**Valid Options:** Verkocht, Facturatie, Inmeet Planning, Inmeet Voltooid, In Productie, Voltooid
**Fix:** Changed to "Verkocht"
**Result:** ✅ 1/1 records syncing

### Issue 7: Projecten - Invalid "Te Reviewen" Status
**Problem:** "Te Reviewen" not in "Verkoop Review Status" options
**Valid Options:** In Review, Goedgekeurd, Afgekeurd
**Fix:** Changed to "In Review"
**Result:** ✅ 1/1 records syncing

---

## Webhook Configuration

**Current URL:** `https://small-terms-cover.loca.lt/webhook/offorte`
**Webhook ID:** 450 (in Offorte)
**Events:** `proposal_won`
**Status:** ✅ Active and receiving webhooks

**How to Restart Webhook:**
```bash
# Terminal 1: Start FastAPI server
python3 -m backend.api.server

# Terminal 2: Start localtunnel
lt --port 8002

# Terminal 3: Update webhook URL in Offorte
PYTHONPATH=. python3 scripts/register_offorte_webhook.py [NEW_URL]
```

---

## Testing Scripts

### Manual Sync Test (Proposal 299654)
```bash
PYTHONPATH=. python3 scripts/test_7_table_sync.py
```

### Debug Individual Tables
```bash
# Test SALES tables transformation
PYTHONPATH=. python3 scripts/test_transformation.py

# Test ADMINISTRATIE sync specifically
PYTHONPATH=. python3 scripts/debug_administratie_sync.py

# Test Nacalculatie sync
PYTHONPATH=. python3 scripts/debug_nacalculatie_sync.py
```

### Verify All Tables
```bash
PYTHONPATH=. python3 -c "
import requests
from backend.core.settings import settings

sales_base = settings.airtable_base_stb_sales
admin_base = settings.airtable_base_stb_administratie
api_key = settings.airtable_api_key
headers = {'Authorization': f'Bearer {api_key}'}

# Check STB-SALES
for table in ['Klantenportaal', 'Elementen Overzicht', 'Nacalculatie']:
    response = requests.get(
        f'https://api.airtable.com/v0/{sales_base}/{table}',
        headers=headers,
        params={'filterByFormula': '{Opdrachtnummer}=\"299654\"'}
    )
    print(f'{table}: {len(response.json().get(\"records\", []))} records')

# Check STB-ADMINISTRATIE
for table in ['Inmeetplanning', 'Projecten']:
    response = requests.get(
        f'https://api.airtable.com/v0/{admin_base}/{table}',
        headers=headers,
        params={'filterByFormula': '{Opdrachtnummer}=\"299654\"'}
    )
    print(f'{table}: {len(response.json().get(\"records\", []))} records')
"
```

---

## Known Limitations & Future Enhancements

### Current Limitations
1. **Sync timeout for large proposals** - 75+ records may timeout (120s limit)
   - Actual sync completes successfully, test script times out
   - Consider background job processing for large proposals

2. **Product Catalogus is passive** - No automatic matching implemented yet
   - Catalog exists with 36 products
   - Cost price lookup NOT automated

3. **API Rate Limiting** - Offorte API can return 429 errors
   - Sync retries handled by Redis queue
   - Consider implementing exponential backoff

### Planned Enhancements
1. **Product Matching** - Implement automatic cost price lookup from Product Catalogus
2. **Facturatie Sync** - Add invoicing workflow table to STB-ADMINISTRATIE
3. **Batch Upsert** - Use Airtable's batch API (10 records at once) instead of sequential
4. **Error Recovery** - Better handling of partial sync failures

---

## Environment Variables Required

```bash
# Offorte API
OFFORTE_API_KEY=your_offorte_api_key_here
OFFORTE_ACCOUNT_NAME=stb-kozijnen

# Airtable API
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_STB-SALES=app9mz6mT0zk8XRGm
AIRTABLE_BASE_STB-ADMINISTRATIE=appuXCPmvIwowH78k

# Server
SERVER_PORT=8002
WEBHOOK_SECRET=generate_random_secret_for_signature_validation

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## Troubleshooting Guide

### Webhook Not Receiving Events
1. Check if localtunnel is running: `curl https://small-terms-cover.loca.lt`
2. Check FastAPI server logs for incoming requests
3. Verify webhook URL in Offorte matches current tunnel URL
4. Re-register webhook if URL changed

### Sync Failing with 422 Errors
1. Check Airtable field schema: Valid options for singleSelect fields
2. Review transformation output for invalid values
3. Ensure `_clean_record_data()` is removing empty/None values
4. Check error logs for specific field causing issue

### Records Not Appearing in Airtable
1. Verify base ID is correct in `.env`
2. Check if transformation created records (review logs)
3. Confirm key field (e.g., "Opdrachtnummer") is present
4. Test with debug script for specific table

### Timeout Issues
1. Increase timeout in test scripts (default: 120s)
2. Check if sync actually completed (verify Airtable directly)
3. Consider reducing logging verbosity to speed up sync

---

## Success Metrics

**Test Proposal:** 299654 (Wouter Bruins)
**Total Records Created:** 75 across 7 tables
**Sync Success Rate:** 100% (75/75 records)
**Average Sync Time:** ~2 minutes for 75 records

**Breakdown:**
- Klantenportaal: 1/1 ✅
- Elementen Overzicht: 9/9 ✅
- Element Specificaties: 9/9 ✅
- Subproducten: 45/45 ✅ (5 subproducts per element)
- Nacalculatie: 9/9 ✅
- Inmeetplanning: 1/1 ✅
- Projecten: 1/1 ✅

---

## Next Steps (Optional)

1. **Implement Product Matching** - Use Product Catalogus for automatic cost price lookup
2. **Add Facturatie Table** - Extend to invoicing workflow
3. **Optimize Batch Sync** - Use Airtable batch API for faster syncing
4. **Add Monitoring** - Track sync success rates, error rates, latency
5. **Webhook Signature Validation** - Implement HMAC validation for security

---

**Status:** ✅ Production Ready
**Maintainer:** Klarifai
**Last Test:** 2025-10-08 00:23 (All tables verified working)
