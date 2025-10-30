#!/usr/bin/env python3
"""Verify that all Airtable tables are set up correctly."""

import requests
from backend.core.settings import settings

# API config
AIRTABLE_API_BASE = "https://api.airtable.com/v0/meta/bases"
headers = {
    "Authorization": f"Bearer {settings.airtable_api_key}",
}

STB_SALES_BASE = settings.airtable_base_stb_sales
STB_ADMIN_BASE = settings.airtable_base_stb_administratie


def get_tables(base_id):
    """Get all tables in a base."""
    url = f"{AIRTABLE_API_BASE}/{base_id}/tables"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("tables", [])
    return []


print("\n" + "="*80)
print("AIRTABLE BASE VERIFICATION")
print("="*80)

# Check STB-SALES
print("\nSTB-SALES Base (app9mz6mT0zk8XRGm)")
print("-" * 80)
sales_tables = get_tables(STB_SALES_BASE)
expected_sales = [
    "Klantenportaal",
    "Elementen Overzicht",
    "Hoofdproduct Specificaties",  # Renamed from Element Specificaties
    "Subproducten",
    "Subproducten Kostprijzen",  # NEW table
    "Nacalculatie"
]

print(f"Found {len(sales_tables)} tables:")
for table in sales_tables:
    status = "[OK]" if table['name'] in expected_sales else "[OLD]"
    print(f"  {status} {table['name']}")

# Check STB-ADMINISTRATIE
print("\nSTB-ADMINISTRATIE Base (appuXCPmvIwowH78k)")
print("-" * 80)
admin_tables = get_tables(STB_ADMIN_BASE)
expected_admin = [
    "Projecten",
    "Facturatie",
    "Inmeetplanning"
]
keep_admin = ["Medewerkers", "Bedrijfsmiddelen"]

print(f"Found {len(admin_tables)} tables:")
for table in admin_tables:
    if table['name'] in expected_admin:
        status = "[OK]"
    elif table['name'] in keep_admin:
        status = "[KEEP]"
    else:
        status = "[OLD]"
    print(f"  {status} {table['name']}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

sales_ok = all(any(t['name'] == exp for t in sales_tables) for exp in expected_sales)
admin_ok = all(any(t['name'] == exp for t in admin_tables) for exp in expected_admin)

if sales_ok and admin_ok:
    print("[OK] All required tables are present!")
    print("\nSTB-SALES: 5/5 tables")
    print("STB-ADMINISTRATIE: 3/3 tables")
    print("\nReady for sync implementation!")
else:
    print("[FAIL] Some tables are missing")
    if not sales_ok:
        missing = [t for t in expected_sales if not any(st['name'] == t for st in sales_tables)]
        print(f"  Missing in STB-SALES: {', '.join(missing)}")
    if not admin_ok:
        missing = [t for t in expected_admin if not any(at['name'] == t for at in admin_tables)]
        print(f"  Missing in STB-ADMINISTRATIE: {', '.join(missing)}")
