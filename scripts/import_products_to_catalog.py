#!/usr/bin/env python3
"""
Import products from STB-Inkoop "Producten" table to STB-SALES "Product Catalogus" table.
from backend.core.settings import settings

This creates the initial product catalog from existing product data.
"""

import requests
import time

# API Configuration
# API_KEY removed - use settings
INKOOP_BASE_ID = "appmEMqFK46AgRg9x"
SALES_BASE_ID = "app9mz6mT0zk8XRGm"

HEADERS = {
    "Authorization": f"Bearer {settings.airtable_api_key}",
    "Content-Type": "application/json"
}

# Category mapping from Inkoop to Catalogus
CATEGORY_MAP = {
    "Windows": "Overig",
    "Doors": "Overig",
    "Hardware": "Beslag",
    "Glazing": "Glas",
    "Installation": "Onderdeel",
}

# Unit mapping
UNIT_MAP = {
    "Each": "Stuk",
    "m2": "m²",
    "Linear Meter": "m¹",
    "Set": "Set",
}


def fetch_producten_from_inkoop():
    """Fetch all products from STB-Inkoop Producten table."""

    url = f"https://api.airtable.com/v0/{INKOOP_BASE_ID}/Producten"

    print("Fetching products from STB-Inkoop...")

    all_records = []
    params = {}

    while True:
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            all_records.extend(records)

            # Check for pagination
            offset = data.get("offset")
            if offset:
                params["offset"] = offset
                time.sleep(0.2)  # Rate limit
            else:
                break
        else:
            print(f"[FAIL] Failed to fetch products: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error: {error_detail}")
            except:
                print(f"Response: {response.text}")
            return None

    print(f"[OK] Fetched {len(all_records)} products from STB-Inkoop")
    return all_records


def transform_product_to_catalog(inkoop_record):
    """Transform a product from Inkoop format to Product Catalogus format."""

    fields = inkoop_record.get("fields", {})

    # Map category
    inkoop_category = fields.get("Productcategorie")
    catalog_category = CATEGORY_MAP.get(inkoop_category, "Overig")

    # Map unit
    inkoop_unit = fields.get("Standaard Meeteenheid")
    catalog_unit = UNIT_MAP.get(inkoop_unit, "Stuk")

    catalog_record = {
        "Product Naam": fields.get("Productnaam", ""),
        "Product ID": fields.get("Product Code", ""),
        "Categorie": catalog_category,
        "Eenheid": catalog_unit,
        "Leverancier": fields.get("Leverancier Naam", ""),
        "Actief": True,
        "Bron": "STB-Inkoop",
        "Notities": fields.get("Productbeschrijving", ""),
    }

    # Remove empty values
    catalog_record = {k: v for k, v in catalog_record.items() if v not in [None, "", False]}

    # Actief must stay
    catalog_record["Actief"] = True

    return catalog_record


def upsert_to_catalog(records, batch_size=10):
    """Upsert records to Product Catalogus table in batches."""

    url = f"https://api.airtable.com/v0/{SALES_BASE_ID}/Product Catalogus"

    print(f"\nUpserting {len(records)} products to Product Catalogus...")

    success_count = 0
    fail_count = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        payload = {
            "records": [{"fields": record} for record in batch],
            "performUpsert": {
                "fieldsToMergeOn": ["Product ID"]
            }
        }

        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            result = response.json()
            created_count = len([r for r in result.get("records", []) if r.get("createdTime")])
            updated_count = len(result.get("records", [])) - created_count
            success_count += len(result.get("records", []))

            print(f"  Batch {i // batch_size + 1}: {created_count} created, {updated_count} updated")
        else:
            fail_count += len(batch)
            print(f"  Batch {i // batch_size + 1} FAILED: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"    Error: {error_detail}")
            except:
                print(f"    Response: {response.text}")

        time.sleep(0.3)  # Rate limit

    print(f"\n[SUMMARY] {success_count} succeeded, {fail_count} failed")
    return success_count, fail_count


def main():
    """Main import process."""

    print("="*60)
    print("IMPORTING PRODUCTS FROM STB-INKOOP TO PRODUCT CATALOGUS")
    print("="*60)

    # Step 1: Fetch products from Inkoop
    inkoop_records = fetch_producten_from_inkoop()

    if not inkoop_records:
        print("[FAIL] No products to import")
        return

    # Step 2: Transform to catalog format
    print("\nTransforming products to catalog format...")
    catalog_records = []

    for record in inkoop_records:
        try:
            catalog_record = transform_product_to_catalog(record)
            if catalog_record.get("Product Naam"):  # Must have a name
                catalog_records.append(catalog_record)
        except Exception as e:
            print(f"[WARN] Failed to transform record: {e}")
            continue

    print(f"[OK] Transformed {len(catalog_records)} products")

    # Step 3: Upsert to Product Catalogus
    if catalog_records:
        success, fail = upsert_to_catalog(catalog_records)

        print("\n" + "="*60)
        print("IMPORT COMPLETE")
        print(f"  Total products processed: {len(catalog_records)}")
        print(f"  Successfully imported: {success}")
        print(f"  Failed: {fail}")
        print("="*60)


if __name__ == "__main__":
    main()
