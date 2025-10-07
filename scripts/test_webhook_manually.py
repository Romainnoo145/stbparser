#!/usr/bin/env python3
"""Send a manual test webhook to verify the sync works."""

import requests
import json

webhook_url = "https://ten-worlds-enter.loca.lt/webhook/offorte"

# Test payload - simulating Offorte webhook
payload = {
    "event": "proposal_won",
    "proposal_id": 238363,
    "timestamp": "2025-10-07T20:00:00Z"
}

print("Sending test webhook...")
print(f"URL: {webhook_url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

response = requests.post(
    webhook_url,
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=10
)

print(f"\nResponse Status: {response.status_code}")
print(f"Response Body: {json.dumps(response.json(), indent=2)}")
