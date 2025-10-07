#!/usr/bin/env python3
"""
Sync the REAL proposal 299654 (Wouter Bruins) to Nacalculatie.
This proposal was synced via webhook but Nacalculatie was missing.
"""

import requests
import json
from backend.core.settings import settings
from backend.services.proposal_sync import ProposalSyncService

print("="*80)
print("SYNCING REAL PROPOSAL 299654 (Wouter Bruins) TO NACALCULATIE")
print("="*80)

# Check current Elementen Overzicht for this proposal
api_key = settings.airtable_api_key
base_id = settings.airtable_base_stb_sales
headers = {'Authorization': f'Bearer {api_key}'}

url = f"https://api.airtable.com/v0/{base_id}/Elementen Overzicht"
response = requests.get(url, headers=headers, params={'filterByFormula': '{Opdrachtnummer}="299654"'})

if response.status_code == 200:
    data = response.json()
    elements = data.get('records', [])
    print(f"\nProposal 299654 heeft {len(elements)} elementen in Elementen Overzicht")

    for record in elements:
        fields = record.get('fields', {})
        element_id = fields.get('Element ID')
        element_type = fields.get('Hoofdproduct Type')
        totaal = fields.get('Element Totaal Excl BTW', 0)
        print(f"  - {element_id}: {element_type} (€{totaal})")
else:
    print(f"\n[ERROR] Could not fetch elements: {response.status_code}")

# Now re-sync the proposal
print("\n" + "="*80)
print("RE-SYNCING PROPOSAL FROM OFFORTE API")
print("="*80)

sync_service = ProposalSyncService()
result = sync_service.sync_proposal(299654)

print(f"\nSync Result:")
print(f"  Success: {result.get('success')}")
print(f"  Steps: {result.get('steps')}")

if result.get('sync_results'):
    print(f"\n  Table Results:")
    for table, stats in result.get('sync_results', {}).items():
        success = stats.get('success', 0)
        failed = stats.get('failed', 0)
        total = stats.get('total', 0)
        print(f"    {table}: {success}/{total} synced ({failed} failed)")

# Verify Nacalculatie now has the data
print("\n" + "="*80)
print("VERIFYING NACALCULATIE TABLE")
print("="*80)

url = f"https://api.airtable.com/v0/{base_id}/Nacalculatie"
response = requests.get(url, headers=headers, params={'filterByFormula': '{Opdrachtnummer}="299654"'})

if response.status_code == 200:
    data = response.json()
    nacalc_records = data.get('records', [])

    print(f"\nNacalculatie voor 299654: {len(nacalc_records)} records")

    if nacalc_records:
        print("\nNacalculatie records:")
        for record in nacalc_records:
            fields = record.get('fields', {})
            element_id = fields.get('Element ID Ref')
            verkoop = fields.get('Totaal Verkoop Excl BTW', 0)
            print(f"  - {element_id}: Verkoop €{verkoop}")
    else:
        print("\n[PROBLEEM] Nog steeds geen Nacalculatie records!")
else:
    print(f"\n[ERROR] Could not verify: {response.status_code}")

print("\n" + "="*80)
