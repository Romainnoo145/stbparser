#!/usr/bin/env python3
"""Debug why Nacalculatie sync fails for proposal 299654."""

import requests
import json
from backend.core.settings import settings
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records

print("="*80)
print("DEBUG: NACALCULATIE SYNC FOR PROPOSAL 299654")
print("="*80)

# Fetch proposal from Offorte API
from urllib.parse import quote
account_name = quote(settings.offorte_account_name)
api_key = settings.offorte_api_key
base_url = f"https://connect.offorte.com/api/v2/{account_name}"

print("\n1. Fetching proposal 299654 from Offorte...")
url = f"{base_url}/proposals/299654/details"
params = {"api_key": api_key}

response = requests.get(url, params=params, timeout=30)

if response.status_code in [200, 201]:
    proposal_data = response.json()
    print(f"   [OK] Fetched proposal")
    print(f"   Customer: {proposal_data.get('contact', {}).get('fullname', 'Unknown')}")
    print(f"   Pricetables: {len(proposal_data.get('pricetables', []))}")
else:
    print(f"   [FAIL] Status {response.status_code}")
    exit(1)

# Transform
print("\n2. Transforming to Airtable records...")
all_records = transform_proposal_to_all_records(proposal_data)

nacalc_records = all_records.get('nacalculatie', [])
print(f"   [OK] Created {len(nacalc_records)} Nacalculatie records")

if nacalc_records:
    print("\n   Sample record:")
    sample = nacalc_records[0]
    for key, value in sample.items():
        print(f"     {key}: {value}")

# Direct sync with detailed error handling
print("\n3. Syncing to Airtable Nacalculatie table...")

airtable_api_key = settings.airtable_api_key
base_id = settings.airtable_base_stb_sales
url = f"https://api.airtable.com/v0/{base_id}/Nacalculatie"

headers = {
    "Authorization": f"Bearer {airtable_api_key}",
    "Content-Type": "application/json"
}

success_count = 0
fail_count = 0

for idx, record in enumerate(nacalc_records, 1):
    element_id = record.get('Element ID Ref')
    print(f"\n   Record {idx}/{len(nacalc_records)}: {element_id}")

    # Clean record
    clean_record = {k: v for k, v in record.items() if v is not None}

    # Show what we're sending
    print(f"     Sending fields: {list(clean_record.keys())}")

    payload = {
        "fields": clean_record,
        "typecast": True
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        result = response.json()
        record_id = result.get('id')
        print(f"     [OK] Created {record_id}")
        success_count += 1
    else:
        print(f"     [FAIL] Status {response.status_code}")
        fail_count += 1

        try:
            error = response.json()
            print(f"     Error: {error}")

            # Show detailed field errors
            if 'error' in error and 'message' in error['error']:
                print(f"     Message: {error['error']['message']}")
        except:
            print(f"     Response: {response.text[:200]}")

print(f"\n4. Results: {success_count} succeeded, {fail_count} failed")

# Verify
print("\n5. Verifying Nacalculatie table...")
response = requests.get(url, headers=headers, params={'filterByFormula': '{Opdrachtnummer}="299654"'})

if response.status_code == 200:
    data = response.json()
    records = data.get('records', [])
    print(f"   [OK] Nacalculatie now has {len(records)} records for proposal 299654")
else:
    print(f"   [FAIL] Could not verify: {response.status_code}")

print("\n" + "="*80)
