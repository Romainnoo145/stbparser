#!/usr/bin/env python3
"""Add real STB products to Product Catalogus based on common items in proposals."""

import requests
import time
from backend.core.settings import settings

API_KEY = settings.airtable_api_key
SALES_BASE_ID = settings.airtable_base_stb_sales

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Real STB products found in proposals
REAL_STB_PRODUCTS = [
    # Glas producten
    {"Product Naam": "Hardstenen onderdorpel", "Categorie": "Onderdeel", "Eenheid": "Stuk"},
    {"Product Naam": "Triple glas", "Categorie": "Glas", "Eenheid": "m²"},
    {"Product Naam": "HR++ glas", "Categorie": "Glas", "Eenheid": "m²"},
    {"Product Naam": "HR+++ glas", "Categorie": "Glas", "Eenheid": "m²"},
    {"Product Naam": "Veiligheidsglas", "Categorie": "Glas", "Eenheid": "m²"},
    {"Product Naam": "Dubbel glas", "Categorie": "Glas", "Eenheid": "m²"},
    {"Product Naam": "Gelaagd glas", "Categorie": "Glas", "Eenheid": "m²"},

    # Beslag
    {"Product Naam": "Hang- en sluitwerk", "Categorie": "Beslag", "Eenheid": "Set"},
    {"Product Naam": "Hang- en sluitwerk met 3-puntsluiting", "Categorie": "Beslag", "Eenheid": "Set"},
    {"Product Naam": "Gelijksluitende cilinders", "Categorie": "Beslag", "Eenheid": "Stuk"},
    {"Product Naam": "Deurbeslag", "Categorie": "Beslag", "Eenheid": "Set"},
    {"Product Naam": "Raambeslag", "Categorie": "Beslag", "Eenheid": "Set"},

    # Hordeuren
    {"Product Naam": "Plissehordeur", "Categorie": "Hordeur", "Eenheid": "Stuk"},
    {"Product Naam": "Insectenhor", "Categorie": "Hordeur", "Eenheid": "Stuk"},
    {"Product Naam": "Raamhordeur", "Categorie": "Hordeur", "Eenheid": "Stuk"},
    {"Product Naam": "Deurhordeur", "Categorie": "Hordeur", "Eenheid": "Stuk"},
    {"Product Naam": "Schuifhordeur", "Categorie": "Hordeur", "Eenheid": "Stuk"},

    # Dakramen
    {"Product Naam": "Keylite dakraam", "Categorie": "Overig", "Eenheid": "Stuk"},
    {"Product Naam": "Velux dakraam", "Categorie": "Overig", "Eenheid": "Stuk"},

    # Kozijnen
    {"Product Naam": "Kunststof kozijn", "Categorie": "Profiel", "Eenheid": "Stuk"},
    {"Product Naam": "Aluminium kozijn", "Categorie": "Profiel", "Eenheid": "Stuk"},
    {"Product Naam": "Houten kozijn", "Categorie": "Profiel", "Eenheid": "Stuk"},

    # Dorpels
    {"Product Naam": "Dorpel aluminium", "Categorie": "Onderdeel", "Eenheid": "Stuk"},
    {"Product Naam": "Buitendorpel", "Categorie": "Onderdeel", "Eenheid": "Stuk"},
    {"Product Naam": "Binnendorpel", "Categorie": "Onderdeel", "Eenheid": "Stuk"},
    {"Product Naam": "Hardstenen dorpel", "Categorie": "Onderdeel", "Eenheid": "Stuk"},

    # Kit en afwerking
    {"Product Naam": "Kit", "Categorie": "Onderdeel", "Eenheid": "Stuk"},
    {"Product Naam": "Afdichtingskit", "Categorie": "Onderdeel", "Eenheid": "Stuk"},
    {"Product Naam": "Siliconenkit", "Categorie": "Onderdeel", "Eenheid": "Stuk"},
    {"Product Naam": "Afwerkingsset", "Categorie": "Onderdeel", "Eenheid": "Set"},
]


def add_stb_products():
    """Add real STB products to Product Catalogus."""

    url = f"https://api.airtable.com/v0/{SALES_BASE_ID}/Product Catalogus"

    print("="*70)
    print("ADDING REAL STB PRODUCTS TO PRODUCT CATALOGUS")
    print("="*70)
    print(f"\nAdding {len(REAL_STB_PRODUCTS)} products...\n")

    # Prepare records
    records = []
    for product in REAL_STB_PRODUCTS:
        # Generate Product ID
        product_id = (product["Product Naam"]
                      .upper()
                      .replace(" ", "-")
                      .replace("+", "PLUS")
                      [:50])

        record = {
            "Product Naam": product["Product Naam"],
            "Product ID": product_id,
            "Categorie": product["Categorie"],
            "Eenheid": product["Eenheid"],
            "Actief": True,
            "Bron": "Handmatig",
            "Matching Keywords": product["Product Naam"].lower(),
        }

        records.append(record)

    # Upsert in batches
    batch_size = 10
    success_count = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        payload = {
            "records": [{"fields": record} for record in batch],
            "performUpsert": {
                "fieldsToMergeOn": ["Product Naam"]
            }
        }

        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            result = response.json()
            count = len(result.get("records", []))
            success_count += count

            print(f"  Batch {i // batch_size + 1}: Added {count} products")

            # Show first batch details
            if i == 0:
                print(f"\n  Sample products:")
                for record in batch[:5]:
                    naam = record["Product Naam"]
                    cat = record["Categorie"]
                    print(f"    - {naam:<40} ({cat})")
                print()
        else:
            print(f"  Batch {i // batch_size + 1}: FAILED ({response.status_code})")
            try:
                error = response.json()
                print(f"    Error: {error}")
            except:
                pass

        time.sleep(0.3)  # Rate limit

    # Show summary by category
    print(f"\n{'='*70}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*70}")
    print(f"\nTotal products added: {success_count}\n")

    # Category breakdown
    from collections import defaultdict
    categories = defaultdict(int)
    for product in REAL_STB_PRODUCTS:
        categories[product["Categorie"]] += 1

    print("Products by category:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat}: {count} products")

    print(f"\n{'='*70}")
    print("Next steps:")
    print("  1. View products in Airtable STB-SALES > Product Catalogus")
    print("  2. Add cost prices manually or match with STB-Inkoop data")
    print("  3. Test product matching in next proposal sync")
    print(f"{'='*70}")

    return success_count


if __name__ == "__main__":
    add_stb_products()
