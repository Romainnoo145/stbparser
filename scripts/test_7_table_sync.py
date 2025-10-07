#!/usr/bin/env python3
"""
Test complete 7-table sync: 5 STB-SALES + 2 STB-ADMINISTRATIE
"""

from backend.services.proposal_sync import ProposalSyncService
import requests
from backend.core.settings import settings

print("="*80)
print("TESTING COMPLETE 7-TABLE SYNC")
print("="*80)
print("\nProposal 299654 (Wouter Bruins)")
print("\nTabellen:")
print("  STB-SALES:")
print("    1. Klantenportaal")
print("    2. Elementen Overzicht")
print("    3. Element Specificaties")
print("    4. Subproducten")
print("    5. Nacalculatie")
print("  STB-ADMINISTRATIE:")
print("    6. Inmeetplanning")
print("    7. Projecten")
print("\n" + "="*80)

# Sync
print("\nSyncing proposal 299654...")
sync_service = ProposalSyncService()
result = sync_service.sync_proposal(299654)

print(f"\nSync Result: {'SUCCESS' if result.get('success') else 'FAILED'}")

if result.get('sync_results'):
    print("\nTable Results:")
    for table, stats in result.get('sync_results', {}).items():
        success = stats.get('success', 0)
        total = stats.get('total', 0)
        status = "[OK]" if success == total else "[PARTIAL]"
        print(f"  {status} {table}: {success}/{total}")

# Verify both bases
print("\n" + "="*80)
print("VERIFYING DATA IN BEIDE BASES")
print("="*80)

# STB-SALES
sales_base = settings.airtable_base_stb_sales
admin_base = settings.airtable_base_stb_administratie
api_key = settings.airtable_api_key
headers = {'Authorization': f'Bearer {api_key}'}

sales_tables = ['Klantenportaal', 'Elementen Overzicht', 'Element Specificaties', 'Subproducten', 'Nacalculatie']
admin_tables = ['Inmeetplanning', 'Projecten']

print("\nSTB-SALES:")
for table in sales_tables:
    url = f"https://api.airtable.com/v0/{sales_base}/{table}"
    response = requests.get(url, headers=headers, params={'filterByFormula': '{Opdrachtnummer}="299654"'})

    if response.status_code == 200:
        records = response.json().get('records', [])
        status = "[OK]" if len(records) > 0 else "[LEEG]"
        print(f"  {status} {table}: {len(records)} records")

print("\nSTB-ADMINISTRATIE:")
for table in admin_tables:
    url = f"https://api.airtable.com/v0/{admin_base}/{table}"
    response = requests.get(url, headers=headers, params={'filterByFormula': '{Opdrachtnummer}="299654"'})

    if response.status_code == 200:
        records = response.json().get('records', [])
        status = "[OK]" if len(records) > 0 else "[LEEG]"
        print(f"  {status} {table}: {len(records)} records")

        # Show details
        if records:
            fields = records[0].get('fields', {})
            print(f"       Klantnaam: {fields.get('Klantnaam', 'N/A')}")
            print(f"       Status: {fields.get('Project Status') or fields.get('Projectstatus', 'N/A')}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
