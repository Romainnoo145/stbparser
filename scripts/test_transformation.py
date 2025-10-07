#!/usr/bin/env python3
"""Test transformation of Offorte proposal to Airtable records."""

import json
import requests
from urllib.parse import quote
from backend.core.settings import settings
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records

# Offorte API configuration
account_name = quote(settings.offorte_account_name)
api_key = settings.offorte_api_key
base_url = f"https://connect.offorte.com/api/v2/{account_name}"

print("="*80)
print("TESTING OFFORTE TO AIRTABLE TRANSFORMATION")
print("="*80)

# Fetch a won proposal
print("\nStep 1: Fetching a won proposal from Offorte...")
response = requests.get(
    f"{base_url}/proposals/won/?api_key={api_key}",
    timeout=10
)

if response.status_code not in [200, 201]:
    print(f"[FAIL] Could not fetch proposals: {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

proposals_data = response.json()
if isinstance(proposals_data, dict):
    proposals = proposals_data.get('data', [])
else:
    proposals = proposals_data if isinstance(proposals_data, list) else []

if not proposals:
    print("[FAIL] No won proposals found")
    exit(1)

# Find a proposal with content
selected_proposal = None
for proposal in proposals[:10]:  # Check first 10
    proposal_id = proposal.get('id')

    # Fetch details to check if it has pricetables
    detail_resp = requests.get(
        f"{base_url}/proposals/{proposal_id}/details?api_key={api_key}",
        timeout=10
    )

    if detail_resp.status_code in [200, 201]:
        detail_data = detail_resp.json()
        pricetables_count = len(detail_data.get('pricetables', []))

        print(f"  Checking proposal {proposal_id}: {pricetables_count} pricetables")

        if pricetables_count > 0:
            selected_proposal = detail_data
            proposal_summary = proposal
            break

if not selected_proposal:
    print("[FAIL] No proposals with pricetables found")
    exit(1)

proposal_id = str(selected_proposal.get('id'))

print(f"\n[OK] Selected proposal: {proposal_id}")
print(f"     Title: {proposal_summary.get('title')}")

# We already have the full proposal data
proposal_data = selected_proposal
print(f"\nStep 2: Using proposal data (already fetched)")

# Show basic info
customer = proposal_data.get('customer', {})
pricetables = proposal_data.get('pricetables', [])
print(f"\nProposal Info:")
print(f"  Customer: {customer.get('company_name') or customer.get('full_name')}")
print(f"  Pricetables: {len(pricetables)}")
print(f"  Total: €{proposal_data.get('pricing', {}).get('total_including_vat', 0):.2f}")

# Transform to Airtable records
print(f"\nStep 3: Transforming to Airtable records...")
try:
    all_records = transform_proposal_to_all_records(proposal_data)
    print("[OK] Transformation successful!")
except Exception as e:
    print(f"[FAIL] Transformation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Show stats
print(f"\nTransformation Results:")
print(f"  Klantenportaal: {len(all_records['klantenportaal'])} record(s)")
print(f"  Elementen Overzicht: {len(all_records['elementen_overzicht'])} record(s)")
print(f"  Element Specificaties: {len(all_records['element_specificaties'])} record(s)")
print(f"  Subproducten: {len(all_records['subproducten'])} record(s)")
print(f"  Nacalculatie: {len(all_records['nacalculatie'])} record(s)")

# Show sample records
print(f"\n" + "="*80)
print("SAMPLE RECORDS")
print("="*80)

if all_records['klantenportaal']:
    print("\nKlantenportaal Record:")
    print(json.dumps(all_records['klantenportaal'][0], indent=2, ensure_ascii=False))

if all_records['elementen_overzicht']:
    print("\nFirst Element Record:")
    print(json.dumps(all_records['elementen_overzicht'][0], indent=2, ensure_ascii=False))

if all_records['element_specificaties']:
    print("\nFirst Element Specs:")
    print(json.dumps(all_records['element_specificaties'][0], indent=2, ensure_ascii=False))

if all_records['subproducten']:
    print(f"\nFirst Subproduct (of {len(all_records['subproducten'])} total):")
    print(json.dumps(all_records['subproducten'][0], indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\nNext step: Run sync_test_proposal.py to actually sync to Airtable")
