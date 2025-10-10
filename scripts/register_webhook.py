#!/usr/bin/env python3
"""Register webhook with Offorte API."""

import requests
import json
import sys
import os
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Offorte API configuration (directly from env to avoid full settings validation)
account_name = quote(os.getenv("OFFORTE_ACCOUNT_NAME"))
api_key = os.getenv("OFFORTE_API_KEY")
base_url = f"https://connect.offorte.com/api/v2/{account_name}"

headers = {
    "Content-Type": "application/json"
}

# Get webhook URL from command line or use default
webhook_url = sys.argv[1] if len(sys.argv) > 1 else "https://noted-symphonically-han.ngrok-free.dev/webhook/offorte"

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
