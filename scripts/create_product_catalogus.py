#!/usr/bin/env python3
"""
Create Product Catalogus table in STB-SALES base.

This table will be the master product catalog for matching and cost price lookups.
"""

import requests
from backend.core.settings import settings

def create_product_catalogus_table():
    """Create the Product Catalogus table in STB-SALES base."""

    base_id = settings.airtable_base_stb_sales
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"

    headers = {
        "Authorization": f"Bearer {settings.airtable_api_key}",
        "Content-Type": "application/json"
    }

    # Table schema
    table_schema = {
        "name": "Product Catalogus",
        "description": "Master product catalog for matching Offorte products with STB product data, cost prices, and supplier information",
        "fields": [
            {
                "name": "Product Naam",
                "type": "singleLineText",
                "description": "Product name as it appears in Offorte/quotes"
            },
            {
                "name": "Product ID",
                "type": "singleLineText",
                "description": "Unique internal product identifier (SKU/article number)"
            },
            {
                "name": "Categorie",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Hordeur", "color": "blueLight2"},
                        {"name": "Glas", "color": "cyanLight2"},
                        {"name": "Beslag", "color": "tealLight2"},
                        {"name": "Profiel", "color": "greenLight2"},
                        {"name": "Onderdeel", "color": "yellowLight2"},
                        {"name": "Dorpel", "color": "orangeLight2"},
                        {"name": "Kit", "color": "redLight2"},
                        {"name": "Overig", "color": "grayLight2"}
                    ]
                },
                "description": "Product category for classification"
            },
            {
                "name": "Standaard Kostprijs",
                "type": "currency",
                "options": {
                    "precision": 2,
                    "symbol": "€"
                },
                "description": "Standard purchase/cost price"
            },
            {
                "name": "Eenheid",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Stuk", "color": "blueLight2"},
                        {"name": "m²", "color": "greenLight2"},
                        {"name": "m¹", "color": "tealLight2"},
                        {"name": "Set", "color": "yellowLight2"}
                    ]
                },
                "description": "Unit of measurement for pricing"
            },
            {
                "name": "Leverancier",
                "type": "singleLineText",
                "description": "Primary supplier name"
            },
            {
                "name": "Leverancier SKU",
                "type": "singleLineText",
                "description": "Supplier's article/SKU number"
            },
            {
                "name": "Matching Keywords",
                "type": "multilineText",
                "description": "Keywords for fuzzy matching (comma-separated), e.g., 'hordeur,hor,screen,insect'"
            },
            {
                "name": "Actief",
                "type": "checkbox",
                "options": {
                    "color": "greenBright",
                    "icon": "check"
                },
                "description": "Is this product currently active in catalog?"
            },
            {
                "name": "Bron",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "STB-Inkoop", "color": "blueLight2"},
                        {"name": "Offorte", "color": "greenLight2"},
                        {"name": "Handmatig", "color": "yellowLight2"}
                    ]
                },
                "description": "Source of this product data"
            },
            {
                "name": "Laatst Gebruikt",
                "type": "date",
                "options": {
                    "dateFormat": {
                        "name": "iso"
                    }
                },
                "description": "Last time this product was used in a quote"
            },
            {
                "name": "Gebruik Frequentie",
                "type": "number",
                "options": {
                    "precision": 0
                },
                "description": "How many times this product has been used"
            },
            {
                "name": "Notities",
                "type": "multilineText",
                "description": "Additional notes, specifications, or comments"
            }
        ]
    }

    print("Creating Product Catalogus table in STB-SALES base...")
    print(f"Base ID: {base_id}")

    response = requests.post(url, headers=headers, json=table_schema)

    if response.status_code in [200, 201]:
        result = response.json()
        table_id = result.get("id")
        print("[OK] Successfully created Product Catalogus table!")
        print(f"   Table ID: {table_id}")
        print(f"   Fields created: {len(result.get('fields', []))}")
        print("\nTable structure:")
        for field in result.get('fields', []):
            field_type = field.get('type')
            field_name = field.get('name')
            print(f"   - {field_name} ({field_type})")

        print("\nNext steps:")
        print("   1. Populate catalog from STB-Inkoop data")
        print("   2. Add product matching to Offorte sync")
        print("   3. Auto-fill cost prices when products match")

        return table_id
    else:
        print(f"[FAIL] Failed to create table: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   Error: {error_detail}")
        except:
            print(f"   Response: {response.text}")
        return None


if __name__ == "__main__":
    create_product_catalogus_table()
