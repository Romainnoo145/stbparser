#!/usr/bin/env python3
"""List all Airtable bases in the workspace to find STB-Inkoop."""

import requests
from backend.core.settings import settings

def list_all_bases():
    """List all bases accessible with the API key."""

    url = "https://api.airtable.com/v0/meta/bases"

    headers = {
        "Authorization": f"Bearer {settings.airtable_api_key}",
        "Content-Type": "application/json"
    }

    print("Fetching all Airtable bases...")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        bases = data.get("bases", [])

        print(f"\nFound {len(bases)} bases:\n")

        for base in bases:
            base_id = base.get("id")
            base_name = base.get("name")
            permission_level = base.get("permissionLevel", "unknown")

            print(f"Name: {base_name}")
            print(f"  ID: {base_id}")
            print(f"  Permission: {permission_level}")
            print()

        # Look for STB-Inkoop specifically
        inkoop_base = next((b for b in bases if "inkoop" in b.get("name", "").lower()), None)
        if inkoop_base:
            print(f"[OK] Found STB-Inkoop base: {inkoop_base.get('id')}")
            print(f"Add this to .env as: AIRTABLE_BASE_STB_INKOOP={inkoop_base.get('id')}")

        return bases
    else:
        print(f"[FAIL] Failed to fetch bases: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"Error: {error_detail}")
        except:
            print(f"Response: {response.text}")
        return None


if __name__ == "__main__":
    list_all_bases()
