#!/usr/bin/env python3
"""Explore STB-Inkoop base structure (excluding kozijnen table)."""

from backend.core.settings import settings
import requests

# STB-Inkoop base ID
BASE_ID = "appmEMqFK46AgRg9x"

def explore_inkoop_base():
    """Explore tables and fields in STB-Inkoop base."""

    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"

    headers = {
        "Authorization": f"Bearer {settings.airtable_api_key}",
        "Content-Type": "application/json"
    }

    print("Exploring STB-Inkoop base structure...\n")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        tables = data.get("tables", [])

        print(f"Found {len(tables)} tables:\n")

        for table in tables:
            table_name = table.get("name")

            # Skip kozijnen table to save tokens
            if "kozijn" in table_name.lower():
                print(f"[SKIPPED] {table_name} (kozijnen table - too large)")
                print()
                continue

            fields = table.get("fields", [])
            print(f"Table: {table_name}")
            print(f"  Fields ({len(fields)}):")

            for field in fields:
                field_name = field.get("name")
                field_type = field.get("type")
                field_desc = field.get("description", "")

                print(f"    - {field_name} ({field_type})")
                if field_desc:
                    print(f"      Description: {field_desc}")

                # Show options for select fields
                if field_type in ["singleSelect", "multipleSelects"]:
                    options = field.get("options", {}).get("choices", [])
                    if options:
                        option_names = [opt.get("name") for opt in options[:5]]  # First 5
                        print(f"      Options: {', '.join(option_names)}" + (
                            "..." if len(options) > 5 else ""))

            print()

        # Summary of useful tables for product catalog
        print("\n[SUMMARY] Tables useful for Product Catalogus:")
        useful_tables = [t for t in tables if "kozijn" not in t.get("name", "").lower()]
        for table in useful_tables:
            print(f"  - {table.get('name')} ({len(table.get('fields', []))} fields)")

        return tables
    else:
        print(f"[FAIL] Failed to fetch tables: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"Error: {error_detail}")
        except:
            print(f"Response: {response.text}")
        return None


if __name__ == "__main__":
    explore_inkoop_base()
