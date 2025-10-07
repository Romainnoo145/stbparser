#!/usr/bin/env python3
"""
Test complete sync to all 5 tables including Nacalculatie.
"""

import requests
import json
from backend.core.settings import settings
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records
from backend.services.airtable_sync import AirtableSync

print("="*80)
print("COMPLETE SYNC TEST - ALL 5 TABLES")
print("="*80)

# Load example proposal
print("\nLoading example proposal...")
with open('docs/offorte_proposal_example.json', 'r', encoding='utf-8') as f:
    proposal_data = json.load(f)

proposal_id = proposal_data.get('id')
print(f"Proposal ID: {proposal_id}")
print(f"Proposal Name: {proposal_data.get('name')}")

# Transform to all records
print("\nTransforming to Airtable records...")
all_records = transform_proposal_to_all_records(proposal_data)

print("\nRecords created:")
for table, records in all_records.items():
    print(f"  - {table}: {len(records)} records")

# Initialize sync service
print("\nInitializing Airtable sync...")
sync_service = AirtableSync()

# Sync each table
print("\n" + "="*80)
print("SYNCING TO AIRTABLE")
print("="*80)

results = {}

# Table mapping
table_mapping = {
    'klantenportaal': 'Klantenportaal',
    'elementen_overzicht': 'Elementen Overzicht',
    'element_specificaties': 'Element Specificaties',
    'subproducten': 'Subproducten',
    'nacalculatie': 'Nacalculatie',
}

for internal_name, airtable_name in table_mapping.items():
    records = all_records.get(internal_name, [])

    if not records:
        print(f"\n{airtable_name}: SKIP (no records)")
        continue

    print(f"\n{airtable_name}: Syncing {len(records)} records...")

    # Sync records
    result_ids = sync_service.upsert_records(airtable_name, records)

    success = sum(1 for r in result_ids if r is not None)
    failed = len(result_ids) - success

    results[airtable_name] = {
        'total': len(records),
        'success': success,
        'failed': failed
    }

    print(f"  Result: {success} succeeded, {failed} failed")

    # Show sample for Nacalculatie
    if internal_name == 'nacalculatie' and records:
        print(f"\n  Sample Nacalculatie record:")
        sample = records[0]
        for key, value in sample.items():
            print(f"    {key}: {value}")

# Summary
print("\n" + "="*80)
print("SYNC COMPLETE - SUMMARY")
print("="*80)

for table, result in results.items():
    status = "[OK]" if result['failed'] == 0 else "[PARTIAL]"
    print(f"{status} {table}:")
    print(f"      {result['success']}/{result['total']} records synced")

print("\n" + "="*80)

# Verify Nacalculatie
print("\nVerifying Nacalculatie table...")
api_key = settings.airtable_api_key
base_id = settings.airtable_base_stb_sales

url = f"https://api.airtable.com/v0/{base_id}/Nacalculatie"
response = requests.get(url, headers={'Authorization': f'Bearer {api_key}'})

if response.status_code == 200:
    data = response.json()
    records = data.get('records', [])
    print(f"[OK] Nacalculatie now has {len(records)} records")

    if records:
        print("\nSample record from Airtable:")
        fields = records[0].get('fields', {})
        for key, value in fields.items():
            print(f"  {key}: {value}")
else:
    print(f"[FAIL] Could not verify: {response.status_code}")

print("\n" + "="*80)
