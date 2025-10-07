#!/usr/bin/env python3
"""Create Facturatie and Inmeetplanning tables in STB-ADMINISTRATIE base."""

import requests
import time
from backend.core.settings import settings

# API config
AIRTABLE_API_BASE = "https://api.airtable.com/v0/meta/bases"
headers = {
    "Authorization": f"Bearer {settings.airtable_api_key}",
    "Content-Type": "application/json"
}

STB_ADMIN_BASE = settings.airtable_base_stb_administratie


def create_table(base_id, table_name, fields):
    """Create a new table with specified fields."""
    url = f"{AIRTABLE_API_BASE}/{base_id}/tables"
    payload = {
        "name": table_name,
        "fields": fields
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"  [OK] Created table: {table_name}")
        return True
    else:
        print(f"  [FAIL] Failed to create {table_name}: {response.status_code}")
        print(f"    Error: {response.text}")
        return False


print("\n" + "="*80)
print("Creating Facturatie and Inmeetplanning Tables in STB-ADMINISTRATIE")
print("="*80)

# Table 1: Facturatie (12 fields)
facturatie_fields = [
    {"name": "Factuur ID", "type": "singleLineText"},
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Type Factuur", "type": "singleSelect", "options": {"choices": [
        {"name": "30% Vooraf"},
        {"name": "65% Bij Start"},
        {"name": "5% Oplevering"}
    ]}},
    {"name": "Bedrag", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Concept"},
        {"name": "Verstuurd"},
        {"name": "Betaald"},
        {"name": "Herinnering"},
        {"name": "Achterstallig"}
    ]}},
    {"name": "Verstuurd op", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Vervaldatum", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Klant", "type": "singleLineText"},
    {"name": "Email", "type": "email"},
    {"name": "Telefoon", "type": "phoneNumber"},
    {"name": "Adres", "type": "singleLineText"},
    {"name": "Factuurtitel", "type": "singleLineText"},
]

print("\nCreating: Facturatie")
create_table(STB_ADMIN_BASE, "Facturatie", facturatie_fields)
time.sleep(1)

# Table 2: Inmeetplanning (23 fields)
inmeetplanning_fields = [
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Klant & Stad", "type": "singleLineText"},
    {"name": "Telefoon", "type": "phoneNumber"},
    {"name": "Elementen", "type": "number", "options": {"precision": 0}},
    {"name": "Uren", "type": "number", "options": {"precision": 1}},
    {"name": "Waarde", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Projectstatus", "type": "singleSelect", "options": {"choices": [
        {"name": "Te Plannen"},
        {"name": "Gepland"},
        {"name": "Voltooid"},
        {"name": "Geannuleerd"}
    ]}},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "E-mail", "type": "email"},
    {"name": "Volledig Adres", "type": "singleLineText"},
    {"name": "Stad", "type": "singleLineText"},
    {"name": "Postcode", "type": "singleLineText"},
    {"name": "Provincie", "type": "singleLineText"},
    {"name": "Opdracht verkocht op", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Total Amount Incl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Aantal Elementen", "type": "number", "options": {"precision": 0}},
    {"name": "Elementen Overzicht", "type": "multilineText"},
    {"name": "Locaties", "type": "multilineText"},
    {"name": "Geschatte Uren", "type": "number", "options": {"precision": 1}},
    {"name": "Planning Notities", "type": "multilineText"},
    {"name": "Uiterlijke montagedatum", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Inmeetdatum", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Start Inmeetplanning Trigger", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
]

print("\nCreating: Inmeetplanning")
create_table(STB_ADMIN_BASE, "Inmeetplanning", inmeetplanning_fields)

print("\n" + "="*80)
print("Done! STB-ADMINISTRATIE now has 3 tables:")
print("  - Projecten")
print("  - Facturatie")
print("  - Inmeetplanning")
print("="*80)
