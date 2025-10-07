#!/usr/bin/env python3
"""Register webhook with Offorte API."""

import requests
import json
from urllib.parse import quote
from backend.core.settings import settings

# Offorte API configuration
account_name = quote(settings.offorte_account_name)
api_key = settings.offorte_api_key
base_url = f"https://connect.offorte.com/api/v2/{account_name}"

headers = {
    "Content-Type": "application/json"
}

# Your public webhook URL
webhook_url = "https://ten-worlds-enter.loca.lt/webhook/offorte"

# Try to register webhook
webhook_payload = {
    "url": webhook_url,
    "events": ["proposal_won"]
}

print(f"Attempting to register webhook at: {base_url}/webhooks")
print(f"Webhook URL: {webhook_url}")
print(f"Events: {webhook_payload['events']}")

try:
    # Try POST to create webhook (using API key as query param)
    response = requests.post(
        f"{base_url}/webhooks?api_key={api_key}",
        headers=headers,
        json=webhook_payload,
        timeout=10
    )

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")

    if response.status_code in [200, 201]:
        print("\n[SUCCESS] Webhook registered successfully!")
    else:
        print(f"\n[FAILED] Failed to register webhook: {response.text}")

except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    print("\nTrying to list existing webhooks instead...")

    try:
        # Try GET to list webhooks
        response = requests.get(
            f"{base_url}/webhooks",
            headers=headers,
            timeout=10
        )
        print(f"Existing webhooks: {json.dumps(response.json(), indent=2)}")
    except Exception as e2:
        print(f"Could not list webhooks: {e2}")
