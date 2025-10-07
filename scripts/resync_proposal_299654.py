#!/usr/bin/env python3
"""Re-sync proposal 299654 to test Nacalculatie table."""

from backend.services.proposal_sync import ProposalSyncService

print("="*80)
print("RE-SYNCING PROPOSAL 299654")
print("="*80)

# Initialize sync service
sync_service = ProposalSyncService()

# Sync proposal
result = sync_service.sync_proposal(299654)

print("\n" + "="*80)
print("SYNC RESULT")
print("="*80)

print(f"Success: {result.get('success')}")
print(f"\nSteps:")
for step, status in result.get('steps', {}).items():
    print(f"  {step}: {status}")

print(f"\nTable Results:")
for table, stats in result.get('table_results', {}).items():
    print(f"  {table}: {stats.get('success', 0)}/{stats.get('total', 0)} records")

if result.get('errors'):
    print(f"\nErrors:")
    for error in result['errors']:
        print(f"  - {error}")

print("\n" + "="*80)

# Check Nacalculatie table
import requests
from backend.core.settings import settings

url = f"https://api.airtable.com/v0/{settings.airtable_base_stb_sales}/Nacalculatie"
response = requests.get(url, headers={'Authorization': f'Bearer {settings.airtable_api_key}'})

if response.status_code == 200:
    data = response.json()
    records = data.get('records', [])

    print(f"\nNacalculatie tabel heeft nu {len(records)} records")

    if records:
        print("\nVoorbeeld record:")
        fields = records[0].get('fields', {})
        for key, value in fields.items():
            print(f"  {key}: {value}")
else:
    print(f"\n[ERROR] Could not check Nacalculatie: {response.status_code}")

print("\n" + "="*80)
