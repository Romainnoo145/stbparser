#!/usr/bin/env python3
"""
Setup Airtable bases with new structure.

This script will:
1. Rename existing tables to "(ARCHIEF)"
2. Create new tables with correct structure
3. Create all fields with proper types
"""

import requests
import json
import time
from backend.core.settings import settings

AIRTABLE_API_KEY = settings.airtable_api_key
AIRTABLE_API_BASE = "https://api.airtable.com/v0/meta/bases"

headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# Base IDs
STB_SALES_BASE = settings.airtable_base_stb_sales
STB_ADMIN_BASE = settings.airtable_base_stb_administratie

print(f"STB-SALES Base: {STB_SALES_BASE}")
print(f"STB-ADMIN Base: {STB_ADMIN_BASE}")
print(f"\n{'='*80}\n")


def get_base_schema(base_id):
    """Get current base schema."""
    url = f"{AIRTABLE_API_BASE}/{base_id}/tables"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting schema: {response.status_code} - {response.text}")
        return None


def rename_table(base_id, table_id, new_name):
    """Rename a table."""
    url = f"{AIRTABLE_API_BASE}/{base_id}/tables/{table_id}"
    payload = {"name": new_name}
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"  [OK] Renamed to: {new_name}")
        return True
    else:
        print(f"  [FAIL] Failed: {response.status_code} - {response.text}")
        return False


def create_table(base_id, table_name, fields):
    """Create a new table with fields."""
    url = f"{AIRTABLE_API_BASE}/{base_id}/tables"

    payload = {
        "name": table_name,
        "fields": fields
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        print(f"  [OK] Created table: {table_name}")
        return response.json()
    else:
        print(f"  [FAIL] Failed to create {table_name}: {response.status_code}")
        print(f"    Error: {response.text}")
        return None


# =============================================================================
# STEP 1: Archive existing tables in STB-SALES
# =============================================================================

print("STEP 1: Archiving existing tables in STB-SALES base...")
print("-" * 80)

sales_schema = get_base_schema(STB_SALES_BASE)
if sales_schema and 'tables' in sales_schema:
    for table in sales_schema['tables']:
        table_name = table['name']
        table_id = table['id']

        if not table_name.endswith("(ARCHIEF)"):
            new_name = f"{table_name} (ARCHIEF)"
            print(f"Archiving: {table_name}")
            rename_table(STB_SALES_BASE, table_id, new_name)
            time.sleep(0.3)  # Rate limiting

print("\n")

# =============================================================================
# STEP 2: Create new tables in STB-SALES
# =============================================================================

print("STEP 2: Creating new tables in STB-SALES base...")
print("-" * 80)

# Table 1: Klantenportaal
klantenportaal_fields = [
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "Adres", "type": "multilineText"},
    {"name": "Telefoon", "type": "singleLineText"},
    {"name": "E-mail", "type": "email"},
    {"name": "Totaalprijs Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Totaalprijs Incl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Offerte Elementen Overzicht", "type": "multilineText"},
    {"name": "Verkoop Notities", "type": "multilineText"},
]

print("Creating: Klantenportaal")
create_table(STB_SALES_BASE, "Klantenportaal", klantenportaal_fields)
time.sleep(0.5)

# Table 2: Elementen Overzicht
elementen_overzicht_fields = [
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Element ID", "type": "singleLineText"},
    {"name": "Element Volgnummer", "type": "number", "options": {"precision": 0}},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Te Reviewen"},
        {"name": "In Review"},
        {"name": "Goedgekeurd"},
        {"name": "Afgekeurd"}
    ]}},

    # Hoofdproduct
    {"name": "Hoofdproduct Type", "type": "singleSelect", "options": {"choices": [
        {"name": "Deur"},
        {"name": "Raam"},
        {"name": "Schuifpui"},
        {"name": "Accessoire"},
        {"name": "Anders"}
    ]}},
    {"name": "Hoofdproduct Naam", "type": "singleLineText"},
    {"name": "Hoofdproduct Beschrijving", "type": "multilineText"},
    {"name": "Hoofdproduct Prijs Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Hoofdproduct Aantal", "type": "number", "options": {"precision": 0}},

    # Subproducten Summary
    {"name": "Subproducten Count", "type": "number", "options": {"precision": 0}},
    {"name": "Subproducten Totaal Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Heeft Hordeuren", "type": "checkbox", "options": {}},

    # Prijzen
    {"name": "Element Subtotaal Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Element Korting", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Element Totaal Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Element BTW Bedrag", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Element BTW Percentage", "type": "number", "options": {"precision": 0}},
    {"name": "Element Totaal Incl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},

    # Review
    {"name": "Review Datum", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Review Door", "type": "singleLineText"},
    {"name": "Verkoop Notities", "type": "multilineText"},
]

print("Creating: Elementen Overzicht")
create_table(STB_SALES_BASE, "Elementen Overzicht", elementen_overzicht_fields)
time.sleep(0.5)

# Table 3: Element Specificaties
element_specs_fields = [
    {"name": "Element ID Ref", "type": "singleLineText"},
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "Element Type", "type": "singleLineText"},
    {"name": "Element Naam", "type": "singleLineText"},
    {"name": "Locatie", "type": "singleLineText"},

    # Afmetingen
    {"name": "Geoffreerde Afmetingen", "type": "singleLineText"},
    {"name": "Breedte (mm)", "type": "number", "options": {"precision": 0}},
    {"name": "Hoogte (mm)", "type": "number", "options": {"precision": 0}},

    # Glas
    {"name": "Glas Type", "type": "singleSelect", "options": {"choices": [
        {"name": "Triple"},
        {"name": "HR++"},
        {"name": "HR+++"},
        {"name": "Veiligheidsglas"},
        {"name": "Dubbelglas"},
        {"name": "Anders"}
    ]}},
    {"name": "Glas Detail", "type": "singleLineText"},

    # Kleur
    {"name": "Kleur Kozijn", "type": "singleLineText"},
    {"name": "Kleur Binnen", "type": "singleLineText"},
    {"name": "Kleur Buiten", "type": "singleLineText"},
    {"name": "Afwerking Type", "type": "singleSelect", "options": {"choices": [
        {"name": "Houtnerf"},
        {"name": "Glad"},
        {"name": "Structuur"},
        {"name": "Poedercoating"}
    ]}},

    # Deur specifiek
    {"name": "Model Deur", "type": "singleLineText"},
    {"name": "Type Profiel/Kozijn", "type": "singleLineText"},
    {"name": "Draairichting", "type": "singleSelect", "options": {"choices": [
        {"name": "Links"},
        {"name": "Rechts"},
        {"name": "Dubbel"}
    ]}},

    # Beslag
    {"name": "Deurbeslag Binnen", "type": "singleLineText"},
    {"name": "Deurbeslag Buiten", "type": "singleLineText"},
    {"name": "Staafgreep Specificatie", "type": "singleLineText"},
    {"name": "Scharnieren Type", "type": "singleLineText"},
    {"name": "Type Cilinder", "type": "singleLineText"},
    {"name": "Cilinder Gelijksluitend", "type": "singleSelect", "options": {"choices": [
        {"name": "Ja"},
        {"name": "Nee"},
        {"name": "N.v.t."}
    ]}},

    # Dorpel
    {"name": "Soort Onderdorpel", "type": "singleLineText"},
    {"name": "Brievenbus", "type": "singleSelect", "options": {"choices": [
        {"name": "Ja"},
        {"name": "Nee"},
        {"name": "N.v.t."}
    ]}},
    {"name": "Afwatering", "type": "singleLineText"},

    # Overig
    {"name": "Binnenafwerking", "type": "singleLineText"},
    {"name": "Extra Opties", "type": "multilineText"},
    {"name": "Verkoop Review Status", "type": "singleLineText"},
    {"name": "Opmerkingen voor Binnendienst", "type": "multilineText"},
]

print("Creating: Element Specificaties")
create_table(STB_SALES_BASE, "Element Specificaties", element_specs_fields)
time.sleep(0.5)

# Table 4: Subproducten
subproducten_fields = [
    {"name": "Element ID Ref", "type": "singleLineText"},
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "Element Type", "type": "singleLineText"},

    {"name": "Subproduct Type", "type": "singleSelect", "options": {"choices": [
        {"name": "Meerprijs"},
        {"name": "Optie"},
        {"name": "Accessoire"},
        {"name": "Korting"}
    ]}},
    {"name": "Subproduct Naam", "type": "singleLineText"},
    {"name": "Subproduct Beschrijving", "type": "multilineText"},
    {"name": "Subproduct Categorie", "type": "singleSelect", "options": {"choices": [
        {"name": "Kleur"},
        {"name": "Glas"},
        {"name": "Beslag"},
        {"name": "Hordeur"},
        {"name": "Ventilatie"},
        {"name": "Dorpel"},
        {"name": "Anders"}
    ]}},
    {"name": "Bron", "type": "singleSelect", "options": {"choices": [
        {"name": "Offorte"},
        {"name": "Handmatig Toegevoegd"}
    ]}},

    {"name": "Prijs Per Stuk Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Aantal", "type": "number", "options": {"precision": 0}},
    {"name": "Subtotaal Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},

    {"name": "Product ID", "type": "singleLineText"},
    {"name": "SKU", "type": "singleLineText"},

    {"name": "Kostprijs Per Stuk", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Kostprijs Totaal", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Marge Percentage", "type": "number", "options": {"precision": 1}},
]

print("Creating: Subproducten")
create_table(STB_SALES_BASE, "Subproducten", subproducten_fields)
time.sleep(0.5)

# Table 5: Nacalculatie
nacalculatie_fields = [
    {"name": "Element ID Ref", "type": "singleLineText"},
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "Element Type", "type": "singleLineText"},

    {"name": "Hoofdproduct Verkoop", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Subproducten Verkoop", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Totaal Verkoop Excl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Totaal Verkoop Incl BTW", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Verkoop Datum", "type": "date", "options": {"dateFormat": {"name": "iso"}}},

    {"name": "Hoofdproduct Kostprijs", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Materiaal Kostprijs", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Arbeid Kostprijs", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Subproducten Kostprijs", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Transport Kosten", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Overige Kosten", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Totale Kostprijs", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Kostprijs Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Te Berekenen"},
        {"name": "Berekend"},
        {"name": "Definitief"}
    ]}},

    {"name": "Bruto Marge Euro", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
    {"name": "Bruto Marge Percentage", "type": "number", "options": {"precision": 1}},
    {"name": "Marge Categorie", "type": "singleSelect", "options": {"choices": [
        {"name": "Uitstekend (>40%)"},
        {"name": "Goed (30-40%)"},
        {"name": "Matig (20-30%)"},
        {"name": "Slecht (<20%)"}
    ]}},
    {"name": "Marge Opmerking", "type": "multilineText"},

    {"name": "Nacalculatie Door", "type": "singleLineText"},
    {"name": "Nacalculatie Datum", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Goedgekeurd Door", "type": "singleLineText"},
]

print("Creating: Nacalculatie")
create_table(STB_SALES_BASE, "Nacalculatie", nacalculatie_fields)
time.sleep(0.5)

print("\n")

# =============================================================================
# STEP 3: Archive existing tables in STB-ADMINISTRATIE
# =============================================================================

print("STEP 3: Archiving existing tables in STB-ADMINISTRATIE base...")
print("-" * 80)

admin_schema = get_base_schema(STB_ADMIN_BASE)
if admin_schema and 'tables' in admin_schema:
    for table in admin_schema['tables']:
        table_name = table['name']
        table_id = table['id']

        # Skip Medewerkers and Bedrijfsmiddelen - those stay
        if table_name in ["Medewerkers", "Bedrijfsmiddelen"]:
            print(f"Keeping: {table_name} (no changes)")
            continue

        if not table_name.endswith("(ARCHIEF)"):
            new_name = f"{table_name} (ARCHIEF)"
            print(f"Archiving: {table_name}")
            rename_table(STB_ADMIN_BASE, table_id, new_name)
            time.sleep(0.3)

print("\n")

# =============================================================================
# STEP 4: Create new tables in STB-ADMINISTRATIE
# =============================================================================

print("STEP 4: Creating new tables in STB-ADMINISTRATIE base...")
print("-" * 80)

# Table 1: Projecten (NEW)
projecten_fields = [
    {"name": "Opdrachtnummer", "type": "singleLineText"},
    {"name": "Klantnaam", "type": "singleLineText"},
    {"name": "Project Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Nieuw"},
        {"name": "Facturatie"},
        {"name": "Inmeet Planning"},
        {"name": "Inmeet Voltooid"},
        {"name": "In Productie"},
        {"name": "Voltooid"}
    ]}},

    {"name": "Volledig Adres", "type": "multilineText"},
    {"name": "Postcode", "type": "singleLineText"},
    {"name": "Stad", "type": "singleLineText"},
    {"name": "Telefoon", "type": "singleLineText"},
    {"name": "Email", "type": "email"},

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
    {"name": "Inmeet Voltooid", "type": "checkbox", "options": {}},
]

print("Creating: Projecten")
create_table(STB_ADMIN_BASE, "Projecten", projecten_fields)
time.sleep(0.5)

# Recreate Facturatie and Inmeetplanning (keeping same structure as archived)
print("\nNote: Facturatie and Inmeetplanning tables archived.")
print("You may want to manually recreate them or they'll be created on first sync.")

print("\n")
print("="*80)
print("DONE! All tables have been set up.")
print("="*80)
print("\nSummary:")
print("  STB-SALES: 5 new tables created")
print("    - Klantenportaal")
print("    - Elementen Overzicht")
print("    - Element Specificaties")
print("    - Subproducten")
print("    - Nacalculatie")
print("\n  STB-ADMINISTRATIE: 1 new table created")
print("    - Projecten")
print("\n  Old tables renamed with (ARCHIEF) suffix")
