#!/usr/bin/env python3
"""Fetch a proposal from Offorte API to see data structure."""

import requests
import json
from urllib.parse import quote
from backend.core.settings import settings

# Offorte API configuration
account_name = quote(settings.offorte_account_name)
api_key = settings.offorte_api_key
base_url = f"https://connect.offorte.com/api/v2/{account_name}"

# Try different auth methods
auth_methods = [
    {"Authorization": f"Bearer {api_key}"},
    {"Authorization": f"Token {api_key}"},
    {"X-API-Key": api_key},
]

print(f"Account: {settings.offorte_account_name}")
print(f"Base URL: {base_url}")
print(f"API Key (first 10 chars): {api_key[:10]}...\n")

# First, try to list proposals (using /proposals/won/ endpoint)
for i, headers in enumerate(auth_methods, 1):
    print(f"Attempt {i}: {list(headers.keys())[0]}")
    try:
        # Try won proposals first
        response = requests.get(
            f"{base_url}/proposals/won/",
            headers=headers,
            timeout=10
        )

        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  SUCCESS! Found {len(data.get('data', []))} proposals")

            if data.get('data'):
                # Show first proposal
                proposal = data['data'][0]
                print(f"\n  First proposal ID: {proposal.get('id')}")
                print(f"  Title: {proposal.get('title', 'N/A')}")
                print(f"  Status: {proposal.get('status', 'N/A')}")

                # Now fetch full proposal details
                proposal_id = proposal.get('id')
                print(f"\n  Fetching full details for proposal {proposal_id}...")

                detail_response = requests.get(
                    f"{base_url}/proposals/{proposal_id}/details",
                    headers=headers,
                    timeout=10
                )

                if detail_response.status_code == 200:
                    print(f"\n  Full proposal data:")
                    print(json.dumps(detail_response.json(), indent=2)[:2000])
                    print("\n  [Truncated - showing first 2000 chars]")

                    # Save to file
                    with open('/tmp/offorte_proposal_sample.json', 'w') as f:
                        json.dump(detail_response.json(), f, indent=2)
                    print("\n  Saved full data to: /tmp/offorte_proposal_sample.json")
                else:
                    print(f"  Could not fetch details: {detail_response.status_code}")
            break
        else:
            print(f"  Failed: {response.text[:200]}")

    except Exception as e:
        print(f"  Error: {e}")

    print()

print("\nIf none worked, check:")
print("1. Is the API key correct in .env?")
print("2. Is the account name correct?")
print("3. Does the API key have the right permissions?")
