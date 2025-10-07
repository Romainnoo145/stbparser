#!/usr/bin/env python3
"""Create the two tables that failed due to checkbox validation error."""

import requests
import time
from backend.core.settings import settings

# API config
AIRTABLE_API_BASE = "https://api.airtable.com/v0/meta/bases"
headers = {
    "Authorization": f"Bearer {settings.airtable_api_key}",
    "Content-Type": "application/json"
}

STB_SALES_BASE = settings.airtable_base_stb_sales
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
print("Creating Missing Tables")
print("="*80)

# Table 1: Elementen Overzicht
elementen_overzicht_fields = [
    # Identificatie
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Element ID", "type": "singleLineText"},
    {"name": "Element Volgnummer", "type": "number", "options": {"precision": 0}},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Nieuw"},
        {"name": "In Review"},
        {"name": "Goedgekeurd"},
        {"name": "In Productie"},
        {"name": "Voltooid"}
    ]}},

    # Hoofdproduct
    {"name": "Hoofdproduct Type", "type": "singleSelect", "options": {"choices": [
        {"name": "Deur"},
        {"name": "Raam"},
        {"name": "Kozijn"},
        {"name": "Schuifpui"},
        {"name": "Vouwwand"},
        {"name": "Overig"}
    ]}},
    {"name": "Hoofdproduct Naam", "type": "singleLineText"},
    {"name": "Hoofdproduct Beschrijving", "type": "multilineText"},
    {"name": "Hoofdproduct Prijs Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Hoofdproduct Aantal", "type": "number", "options": {"precision": 0}},

    # Subproducten Summary
    {"name": "Subproducten Count", "type": "number", "options": {"precision": 0}},
    {"name": "Subproducten Totaal Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Heeft Hordeuren", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},

    # Prijzen
    {"name": "Element Subtotaal Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Element Korting", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Element Totaal Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Element BTW Bedrag", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Element BTW Percentage", "type": "percent", "options": {"precision": 0}},
    {"name": "Element Totaal Incl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},

    # Nacalculatie Summary (rollups/formulas)
    {"name": "Kostprijs Totaal", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Marge Euro", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Marge Percentage", "type": "percent", "options": {"precision": 1}},

    # Review
    {"name": "Review Datum", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Review Door", "type": "singleLineText"},
    {"name": "Verkoop Notities", "type": "multilineText"},
]

print("\nCreating: Elementen Overzicht")
create_table(STB_SALES_BASE, "Elementen Overzicht", elementen_overzicht_fields)
time.sleep(1)

# Table 2: Projecten
projecten_fields = [
    # Identificatie
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "Project Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Verkocht"},
        {"name": "Facturatie"},
        {"name": "Inmeet Planning"},
        {"name": "Inmeet Voltooid"},
        {"name": "In Productie"},
        {"name": "Voltooid"}
    ]}},

    # Klant Info
    {"name": "Volledig Adres", "type": "singleLineText"},
    {"name": "Postcode", "type": "singleLineText"},
    {"name": "Stad", "type": "singleLineText"},
    {"name": "Telefoon", "type": "phoneNumber"},
    {"name": "Email", "type": "email"},

    # Sales Context
    {"name": "Totaal Verkoopprijs Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Totaal Verkoopprijs Incl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Aantal Elementen", "type": "number", "options": {"precision": 0}},
    {"name": "Elementen Samenvatting", "type": "multilineText"},
    {"name": "Verkoop Review Status", "type": "singleSelect", "options": {"choices": [
        {"name": "In Review"},
        {"name": "Goedgekeurd"},
        {"name": "Afgekeurd"}
    ]}},
    {"name": "Verkoop Notities", "type": "multilineText"},

    {"name": "Inmeetdatum", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Inmeet Notities", "type": "multilineText"},
    {"name": "Inmeet Voltooid", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
]

print("\nCreating: Projecten")
create_table(STB_ADMIN_BASE, "Projecten", projecten_fields)

print("\n" + "="*80)
print("Done!")
print("="*80)
