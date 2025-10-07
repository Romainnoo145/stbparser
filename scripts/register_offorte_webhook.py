#!/usr/bin/env python3
"""Register webhook with Offorte API using correct authentication."""

import requests
import json
import sys
from urllib.parse import quote
from backend.core.settings import settings

# Offorte API configuration
account_name = quote(settings.offorte_account_name)
api_key = settings.offorte_api_key
base_url = f"https://connect.offorte.com/api/v2/{account_name}"

# Current webhook URL (can be overridden via command line)
webhook_url = sys.argv[1] if len(sys.argv) > 1 else "https://ten-worlds-enter.loca.lt/webhook/offorte"

print("="*80)
print("OFFORTE WEBHOOK REGISTRATION")
print("="*80)
print(f"Account: {settings.offorte_account_name}")
print(f"Webhook URL: {webhook_url}")
print()

# Step 1: List existing webhooks
print("Step 1: Checking existing webhooks...")
try:
    response = requests.get(
        f"{base_url}/webhooks?api_key={api_key}",
        timeout=10
    )
    print(f"Status: {response.status_code}")

    if response.status_code in [200, 201]:
        webhooks = response.json()
        print(f"Existing webhooks: {json.dumps(webhooks, indent=2)}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error listing webhooks: {e}")

print()

# Step 2: Update existing webhook (ID 450) or create new one
webhook_id = None
if response.status_code in [200, 201]:
    webhooks = response.json()
    if isinstance(webhooks, list) and len(webhooks) > 0:
        webhook_id = webhooks[0].get("id")

if webhook_id:
    print(f"Step 2: Updating existing webhook (ID: {webhook_id})...")
    webhook_payload = {
        "payload_url": webhook_url,
        "events": ["proposal_won"],
        "active": 1
    }

    try:
        response = requests.patch(
            f"{base_url}/webhooks/{webhook_id}?api_key={api_key}",
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code in [200, 201]:
            print("\n[SUCCESS] Webhook updated!")
            print(f"\nWebhook URL: {webhook_url}")
        else:
            print("\n[FAILED] Could not update webhook")

    except Exception as e:
        print(f"\n[ERROR] {e}")
else:
    print("Step 2: Registering new webhook...")
    webhook_payload = {
        "payload_url": webhook_url,
        "events": ["proposal_won"]
    }

    try:
        response = requests.post(
            f"{base_url}/webhooks?api_key={api_key}",
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code in [200, 201]:
            print("\n[SUCCESS] Webhook registered!")
            print(f"\nNow when you mark a proposal as 'won' in Offorte,")
            print(f"it will send a webhook to: {webhook_url}")
        else:
            print("\n[FAILED] Could not register webhook")

    except Exception as e:
        print(f"\n[ERROR] {e}")

print("\n" + "="*80)
