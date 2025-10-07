#!/usr/bin/env python3
"""Manually sync a proposal to test the complete flow."""

import sys
from backend.services.proposal_sync import sync_service

# Get proposal ID from command line or use default
proposal_id = int(sys.argv[1]) if len(sys.argv) > 1 else None

if not proposal_id:
    print("Usage: python3 scripts/sync_test_proposal.py <proposal_id>")
    print("\nOr finding a won proposal automatically...")

    import requests
    from urllib.parse import quote
    from backend.core.settings import settings

    account_name = quote(settings.offorte_account_name)
    api_key = settings.offorte_api_key
    base_url = f"https://connect.offorte.com/api/v2/{account_name}"

    response = requests.get(
        f"{base_url}/proposals/won/?api_key={api_key}",
        timeout=10
    )

    if response.status_code in [200, 201]:
        proposals_data = response.json()
        proposals = proposals_data if isinstance(proposals_data, list) else proposals_data.get('data', [])

        if proposals:
            proposal_id = proposals[0].get('id')
            print(f"Using first won proposal: {proposal_id}")
        else:
            print("No won proposals found!")
            sys.exit(1)
    else:
        print(f"Failed to fetch proposals: {response.status_code}")
        sys.exit(1)

print("="*80)
print(f"MANUAL SYNC TEST - Proposal {proposal_id}")
print("="*80)

result = sync_service.sync_proposal(proposal_id)

print("\n" + "="*80)
print("SYNC RESULT")
print("="*80)

import json
print(json.dumps(result, indent=2))

if result.get("success"):
    print("\n✓ SYNC SUCCESSFUL!")
else:
    print("\n✗ SYNC FAILED")
    print(f"Errors: {result.get('errors')}")
