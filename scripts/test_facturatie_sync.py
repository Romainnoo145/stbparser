#!/usr/bin/env python3
"""
Test Facturatie sync for proposal 299654
"""

import json
from backend.transformers.administratie_transforms import transform_proposal_to_facturatie
from backend.services.airtable_sync import AirtableSync
import requests
from backend.core.settings import settings
from urllib.parse import quote

print("="*80)
print("TEST FACTURATIE SYNC")
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
    exit(1)

proposal_data = response.json()
customer = proposal_data.get('customer', {})
total = float(proposal_data.get('price_total_original', 0) or 0)
print(f"[OK] {customer.get('company_name') or customer.get('name')}")
print(f"     Total: €{total:,.2f}")

# Transform to 3 invoices
print("\n" + "="*80)
print("TRANSFORMATION")
print("="*80)

invoices = transform_proposal_to_facturatie(proposal_data)
print(f"\nCreated {len(invoices)} invoices:")

for i, invoice in enumerate(invoices, 1):
    print(f"\n{i}. {invoice['Type Factuur']}")
    print(f"   Factuur ID: {invoice['Factuur ID']}")
    print(f"   Bedrag: €{invoice['Bedrag']:,.2f}")
    print(f"   Status: {invoice['Status']}")
    print(f"   Titel: {invoice['Factuurtitel']}")

# Verify percentages add up to 100%
total_percentage = sum([inv['Bedrag'] for inv in invoices])
expected = float(total)
diff = abs(total_percentage - expected)
print(f"\nTotal check: €{total_percentage:,.2f} (expected €{expected:,.2f}, diff: €{diff:.2f})")

# Sync to Airtable
print("\n" + "="*80)
print("SYNCING TO AIRTABLE")
print("="*80)

sync = AirtableSync()

results = {"succeeded": 0, "failed": 0}

for invoice in invoices:
    print(f"\nSyncing {invoice['Factuur ID']}...")
    result = sync.upsert_record("facturatie", invoice)

    if result:
        print(f"  [OK] {result}")
        results["succeeded"] += 1
    else:
        print(f"  [FAIL] Sync failed")
        results["failed"] += 1

print(f"\n{'='*80}")
print(f"RESULTS: {results['succeeded']}/{len(invoices)} succeeded, {results['failed']} failed")
print("="*80)

# Verify in Airtable
print("\nVERIFICATION:")
admin_base = settings.airtable_base_stb_administratie
api_key_airtable = settings.airtable_api_key
headers = {'Authorization': f'Bearer {api_key_airtable}'}

url = f"https://api.airtable.com/v0/{admin_base}/Facturatie"
response = requests.get(
    url,
    headers=headers,
    params={'filterByFormula': '{Opdrachtnummer}="299654"'}
)

if response.status_code == 200:
    records = response.json().get('records', [])
    print(f"[OK] Found {len(records)} invoices in Airtable")

    for record in records:
        fields = record.get('fields', {})
        print(f"  - {fields.get('Factuur ID')}: {fields.get('Type Factuur')} - €{fields.get('Bedrag', 0):,.2f} ({fields.get('Status')})")
else:
    print(f"[ERROR] HTTP {response.status_code}")
