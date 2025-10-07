#!/usr/bin/env python3
"""Fetch actual field names from Airtable tables."""

import requests
from backend.core.settings import settings

# Airtable Meta API
headers = {
    "Authorization": f"Bearer {settings.airtable_api_key}",
    "Content-Type": "application/json"
}

base_id = settings.airtable_base_stb_sales

# Tables to check
tables = [
    "Element Specificaties",
    "Subproducten",
    "Nacalculatie"
]

print("="*80)
print("AIRTABLE FIELD NAMES")
print("="*80)

for table_name in tables:
    print(f"\n{table_name}:")
    print("-"*80)

    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        tables_data = response.json().get("tables", [])

        # Find our table
        table_info = next((t for t in tables_data if t["name"] == table_name), None)

        if table_info:
            fields = table_info.get("fields", [])
            print(f"Found {len(fields)} fields:")
            for field in fields:
                field_name = field.get("name")
                field_type = field.get("type")
                print(f"  - {field_name} ({field_type})")
        else:
            print(f"  Table '{table_name}' not found!")
    else:
        print(f"  Error: {response.status_code}")
        print(f"  {response.text}")

print("\n" + "="*80)
