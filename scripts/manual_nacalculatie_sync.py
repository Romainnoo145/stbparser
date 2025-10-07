#!/usr/bin/env python3
"""
Manually sync Nacalculatie for proposal 299654 to debug why table is empty.
"""

import json
import requests
from backend.core.settings import settings
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records

print("="*80)
print("MANUAL NACALCULATIE SYNC TEST")
print("="*80)

# Use the webhook payload we know exists for 299654
print("\nStep 1: Loading example proposal data...")
with open('docs/offorte_proposal_example.json', 'r') as f:
    proposal_data = json.load(f)

proposal_id = proposal_data.get('id')
print(f"Proposal ID: {proposal_id}")

# Transform
print("\nStep 2: Transforming to Airtable records...")
all_records = transform_proposal_to_all_records(proposal_data)

nacalculatie_records = all_records.get('nacalculatie', [])
print(f"Created {len(nacalculatie_records)} Nacalculatie records")

if nacalculatie_records:
    print("\nSample record:")
    for key, value in nacalculatie_records[0].items():
        print(f"  {key}: {value}")

# Direct API call to Airtable
print("\n" + "="*80)
print("Step 3: Direct sync to Airtable Nacalculatie table")
print("="*80)

api_key = settings.airtable_api_key
base_id = settings.airtable_base_stb_sales

url = f"https://api.airtable.com/v0/{base_id}/Nacalculatie"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Try to create records
for idx, record in enumerate(nacalculatie_records, 1):
    print(f"\nSyncing record {idx}/{len(nacalculatie_records)}...")
    print(f"  Element ID: {record.get('Element ID Ref')}")

    # Clean record (remove None values)
    clean_record = {k: v for k, v in record.items() if v is not None}

    payload = {
        "fields": clean_record,
        "typecast": True  # Auto-convert types
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        result = response.json()
        airtable_id = result.get('id')
        print(f"  [OK] SUCCESS - Created record {airtable_id}")
    else:
        print(f"  [FAIL] FAILED - Status {response.status_code}")
        try:
            error = response.json()
            print(f"  Error: {error}")
        except:
            print(f"  Response: {response.text[:200]}")

# Verify
print("\n" + "="*80)
print("Step 4: Verifying Nacalculatie table")
print("="*80)

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    records = data.get('records', [])

    print(f"\n[OK] Nacalculatie table now has {len(records)} records")

    if records:
        print("\nLatest record from Airtable:")
        fields = records[-1].get('fields', {})
        for key, value in fields.items():
            print(f"  {key}: {value}")
    else:
        print("\n[FAIL] PROBLEM: Table is still empty!")
else:
    print(f"\n[FAIL] Could not verify: {response.status_code}")

print("\n" + "="*80)
