#!/usr/bin/env python3
"""
Debug STB-ADMINISTRATIE sync (Inmeetplanning + Projecten)
"""

import json
from backend.transformers.administratie_transforms import (
    transform_proposal_to_inmeetplanning,
    transform_proposal_to_project
)
from backend.services.airtable_sync import AirtableSync
import requests
from backend.core.settings import settings
from urllib.parse import quote

print("="*80)
print("DEBUG STB-ADMINISTRATIE SYNC")
print("="*80)

# Fetch proposal 299654
proposal_id = 299654
account_name = quote(settings.offorte_account_name)
api_key = settings.offorte_api_key
base_url = f"https://connect.offorte.com/api/v2/{account_name}"

print(f"\nFetching proposal {proposal_id}...")
response = requests.get(
    f"{base_url}/proposals/{proposal_id}/details?api_key={api_key}",
    timeout=10
)

if response.status_code != 200:
    print(f"[FAIL] Could not fetch proposal: {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

proposal_data = response.json()
customer = proposal_data.get('customer', {})
print(f"[OK] Loaded: {customer.get('company_name') or customer.get('name')}")

# Transform
print("\n" + "="*80)
print("TRANSFORMATIONS")
print("="*80)

print("\n1. Inmeetplanning Record:")
inmeet_record = transform_proposal_to_inmeetplanning(proposal_data)
print(json.dumps(inmeet_record, indent=2, ensure_ascii=False))

print("\n2. Projecten Record:")
project_record = transform_proposal_to_project(proposal_data)
print(json.dumps(project_record, indent=2, ensure_ascii=False))

# Sync to Airtable
print("\n" + "="*80)
print("SYNCING TO AIRTABLE")
print("="*80)

sync = AirtableSync()

# Clean records
inmeet_clean = sync._clean_record_data(inmeet_record)
project_clean = sync._clean_record_data(project_record)

print(f"\nCleaned Inmeetplanning ({len(inmeet_clean)} fields):")
print(json.dumps(inmeet_clean, indent=2, ensure_ascii=False))

print(f"\nCleaned Projecten ({len(project_clean)} fields):")
print(json.dumps(project_clean, indent=2, ensure_ascii=False))

# Upsert Inmeetplanning
print("\n" + "-"*80)
print("Syncing to Inmeetplanning...")
inmeet_result = sync.upsert_record("inmeetplanning", inmeet_record)
if inmeet_result:
    print(f"[OK] Inmeetplanning: {inmeet_result}")
else:
    print("[FAIL] Inmeetplanning sync failed - check logs above")

# Upsert Projecten
print("\n" + "-"*80)
print("Syncing to Projecten...")
project_result = sync.upsert_record("projecten", project_record)
if project_result:
    print(f"[OK] Projecten: {project_result}")
else:
    print("[FAIL] Projecten sync failed - check logs above")

# Verify in Airtable
print("\n" + "="*80)
print("VERIFICATION")
print("="*80)

admin_base = settings.airtable_base_stb_administratie
api_key_airtable = settings.airtable_api_key
headers = {'Authorization': f'Bearer {api_key_airtable}'}

for table in ['Inmeetplanning', 'Projecten']:
    url = f"https://api.airtable.com/v0/{admin_base}/{table}"
    response = requests.get(
        url,
        headers=headers,
        params={'filterByFormula': '{Opdrachtnummer}="299654"'}
    )

    if response.status_code == 200:
        records = response.json().get('records', [])
        status = "[OK]" if len(records) > 0 else "[LEEG]"
        print(f"{status} {table}: {len(records)} records")

        if records:
            fields = records[0].get('fields', {})
            print(f"     Klantnaam: {fields.get('Klantnaam', 'N/A')}")
            print(f"     Status: {fields.get('Project Status') or fields.get('Projectstatus', 'N/A')}")
    else:
        print(f"[ERROR] {table}: HTTP {response.status_code}")
        print(f"        {response.text}")

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80)
