#!/usr/bin/env python3
"""
Populate Product Catalogus from existing Offorte data in Subproducten table.
from backend.core.settings import settings

This extracts unique products from sold quotes and adds them to the catalog.
"""

import requests
import time
from collections import defaultdict

# API Configuration
# API_KEY removed - use settings
SALES_BASE_ID = "app9mz6mT0zk8XRGm"

HEADERS = {
    "Authorization": f"Bearer {settings.airtable_api_key}",
    "Content-Type": "application/json"
}


def fetch_subproducten():
    """Fetch all subproducten from STB-SALES to extract unique products."""

    url = f"https://api.airtable.com/v0/{SALES_BASE_ID}/Subproducten"

    print("Fetching subproducten from STB-SALES...")

    all_records = []
    params = {}

    while True:
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            all_records.extend(records)

            offset = data.get("offset")
            if offset:
                params["offset"] = offset
                time.sleep(0.2)
            else:
                break
        else:
            print(f"[FAIL] Failed to fetch subproducten: {response.status_code}")
            return None

    print(f"[OK] Fetched {len(all_records)} subproducten")
    return all_records


def extract_unique_products(subproducten_records):
    """Extract unique products from subproducten."""

    product_stats = defaultdict(lambda: {
        "count": 0,
        "categories": set(),
        "last_used": None,
        "sample_names": []
    })

    for record in subproducten_records:
        fields = record.get("fields", {})

        product_name = fields.get("Productnaam", "").strip()
        if not product_name:
            continue

        category = fields.get("Subproduct Categorie", fields.get("Subproduct Type", "Overig"))
        verkoop_datum = fields.get("Verkoop Datum")

        # Update stats
        stats = product_stats[product_name]
        stats["count"] += 1
        if category:
            stats["categories"].add(category)
        if verkoop_datum:
            if not stats["last_used"] or verkoop_datum > stats["last_used"]:
                stats["last_used"] = verkoop_datum

        # Keep sample names for similar products
        if len(stats["sample_names"]) < 3:
            stats["sample_names"].append(product_name)

    print(f"\n[OK] Found {len(product_stats)} unique products")

    # Convert to catalog records
    catalog_records = []

    for product_name, stats in product_stats.items():
        # Determine category (most common or first)
        category = list(stats["categories"])[0] if stats["categories"] else "Overig"

        # Generate product ID from name
        product_id = product_name.upper().replace(" ", "-")[:50]

        catalog_record = {
            "Product Naam": product_name,
            "Product ID": product_id,
            "Categorie": category,
            "Eenheid": "Stuk",  # Default
            "Actief": True,
            "Bron": "Offorte",
            "Laatst Gebruikt": stats["last_used"],
            "Gebruik Frequentie": stats["count"],
            "Matching Keywords": product_name.lower(),  # Exact name for matching
        }

        # Remove None values
        catalog_record = {k: v for k, v in catalog_record.items() if v is not None}

        catalog_records.append(catalog_record)

    # Sort by frequency (most used first)
    catalog_records.sort(key=lambda x: x.get("Gebruik Frequentie", 0), reverse=True)

    return catalog_records


def upsert_to_catalog(records, batch_size=10):
    """Upsert records to Product Catalogus table."""

    url = f"https://api.airtable.com/v0/{SALES_BASE_ID}/Product Catalogus"

    print(f"\nUpserting {len(records)} products to Product Catalogus...")

    success_count = 0
    fail_count = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        payload = {
            "records": [{"fields": record} for record in batch],
            "performUpsert": {
                "fieldsToMergeOn": ["Product Naam"]  # Match on name
            }
        }

        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            result = response.json()
            batch_count = len(result.get("records", []))
            success_count += batch_count

            # Show top products in first batch
            if i == 0:
                print(f"\n  Top products by usage:")
                for j, record in enumerate(batch[:5], 1):
                    name = record.get("Product Naam", "Unknown")
                    freq = record.get("Gebruik Frequentie", 0)
                    print(f"    {j}. {name} ({freq}x used)")

            print(f"  Batch {i // batch_size + 1}: {batch_count} products")
        else:
            fail_count += len(batch)
            print(f"  Batch {i // batch_size + 1} FAILED: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"    Error: {error_detail}")
            except:
                pass

        time.sleep(0.3)

    print(f"\n[SUMMARY] {success_count} succeeded, {fail_count} failed")
    return success_count, fail_count


def main():
    """Main population process."""

    print("="*60)
    print("POPULATING PRODUCT CATALOGUS FROM OFFORTE DATA")
    print("="*60)

    # Step 1: Fetch subproducten
    subproducten = fetch_subproducten()

    if not subproducten:
        print("[FAIL] No subproducten found")
        return

    # Step 2: Extract unique products
    catalog_records = extract_unique_products(subproducten)

    if not catalog_records:
        print("[FAIL] No products to add")
        return

    # Step 3: Upsert to catalog
    success, fail = upsert_to_catalog(catalog_records)

    print("\n" + "="*60)
    print("CATALOG POPULATION COMPLETE")
    print(f"  Unique products: {len(catalog_records)}")
    print(f"  Successfully added: {success}")
    print(f"  Failed: {fail}")
    print("\n  Next steps:")
    print("    1. Add cost prices manually in Airtable")
    print("    2. Match products with STB-Inkoop data")
    print("    3. Enable automatic cost price lookup in sync")
    print("="*60)


if __name__ == "__main__":
    main()
