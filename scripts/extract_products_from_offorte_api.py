#!/usr/bin/env python3
"""
Extract product catalog from Offorte proposals by analyzing pricetable rows.

This fetches recent won proposals and extracts unique product names.
"""

import requests
import time
from collections import defaultdict
from backend.core.settings import settings

# Offorte API config
OFFORTE_API_KEY = settings.offorte_api_key
OFFORTE_BASE_URL = settings.offorte_base_url

# Airtable config
AIRTABLE_API_KEY = settings.airtable_api_key
SALES_BASE_ID = settings.airtable_base_stb_sales

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}


def fetch_won_proposals(limit=10):
    """Fetch recently won proposals from Offorte."""

    url = f"{OFFORTE_BASE_URL}/proposals"
    params = {
        "api_key": OFFORTE_API_KEY,
        "status": "won",
        "per_page": limit,
    }

    print(f"Fetching {limit} won proposals from Offorte...")

    response = requests.get(url, params=params, timeout=30)

    if response.status_code == 200:
        proposals = response.json()
        print(f"[OK] Fetched {len(proposals)} proposals")
        return proposals
    else:
        print(f"[FAIL] Failed to fetch proposals: {response.status_code}")
        return []


def fetch_proposal_details(proposal_id):
    """Fetch detailed proposal data including pricetables."""

    url = f"{OFFORTE_BASE_URL}/proposals/{proposal_id}"
    params = {"api_key": OFFORTE_API_KEY}

    response = requests.get(url, params=params, timeout=30)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"[WARN] Failed to fetch proposal {proposal_id}")
        return None


def extract_products_from_proposals(proposals):
    """Extract unique product names from proposal pricetables."""

    product_stats = defaultdict(lambda: {
        "count": 0,
        "total_value": 0.0,
        "last_used": None,
        "categories": set(),
    })

    for proposal in proposals:
        proposal_id = proposal.get("id")
        print(f"\n  Analyzing proposal {proposal_id}...")

        # Fetch full details
        details = fetch_proposal_details(proposal_id)
        if not details:
            continue

        pricetables = details.get("pricetables", [])
        won_at = details.get("won_at", "")

        for pricetable in pricetables:
            title = pricetable.get("title", "").strip()
            rows = pricetable.get("rows", [])

            # First row is usually the main product
            if rows and len(rows) > 0:
                main_row = rows[0]
                product_name = main_row.get("description", "").strip()

                if product_name and len(product_name) > 2:
                    # Update stats
                    stats = product_stats[product_name]
                    stats["count"] += 1
                    stats["total_value"] += float(main_row.get("price_total", 0) or 0)

                    if won_at:
                        if not stats["last_used"] or won_at > stats["last_used"]:
                            stats["last_used"] = won_at.split("T")[0]

                    # Try to determine category from product name
                    name_lower = product_name.lower()
                    if "hordeur" in name_lower or "hor" in name_lower:
                        stats["categories"].add("Hordeur")
                    elif "glas" in name_lower or "hr++" in name_lower:
                        stats["categories"].add("Glas")
                    elif "beslag" in name_lower:
                        stats["categories"].add("Beslag")
                    elif "profiel" in name_lower:
                        stats["categories"].add("Profiel")
                    else:
                        stats["categories"].add("Overig")

            # Additional rows are subproducts
            for row_idx, row in enumerate(rows[1:], start=1):
                product_name = row.get("description", "").strip()

                if product_name and len(product_name) > 2:
                    stats = product_stats[product_name]
                    stats["count"] += 1
                    stats["total_value"] += float(row.get("price_total", 0) or 0)

                    if won_at and (not stats["last_used"] or won_at > stats["last_used"]):
                        stats["last_used"] = won_at.split("T")[0]

                    # Categorize
                    name_lower = product_name.lower()
                    if "hordeur" in name_lower:
                        stats["categories"].add("Hordeur")
                    elif "glas" in name_lower:
                        stats["categories"].add("Glas")
                    elif "beslag" in name_lower:
                        stats["categories"].add("Beslag")
                    elif "dorpel" in name_lower:
                        stats["categories"].add("Onderdeel")
                    else:
                        stats["categories"].add("Overig")

        time.sleep(0.1)  # Rate limit

    print(f"\n[OK] Extracted {len(product_stats)} unique products")
    return product_stats


def create_catalog_records(product_stats):
    """Convert product stats to catalog records."""

    catalog_records = []

    for product_name, stats in product_stats.items():
        # Determine category
        if stats["categories"]:
            category = list(stats["categories"])[0]
        else:
            category = "Overig"

        # Generate Product ID
        product_id = product_name.upper().replace(" ", "-").replace("/", "-")[:50]

        catalog_record = {
            "Product Naam": product_name,
            "Product ID": product_id,
            "Categorie": category,
            "Eenheid": "Stuk",
            "Actief": True,
            "Bron": "Offorte",
            "Laatst Gebruikt": stats["last_used"],
            "Gebruik Frequentie": stats["count"],
            "Matching Keywords": product_name.lower(),
        }

        # Remove None values
        catalog_record = {k: v for k, v in catalog_record.items() if v is not None}

        catalog_records.append(catalog_record)

    # Sort by frequency
    catalog_records.sort(key=lambda x: x.get("Gebruik Frequentie", 0), reverse=True)

    return catalog_records


def upsert_to_catalog(records, batch_size=10):
    """Upsert records to Product Catalogus."""

    url = f"https://api.airtable.com/v0/{SALES_BASE_ID}/Product Catalogus"

    print(f"\nUpserting {len(records)} products to Product Catalogus...")

    success_count = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        payload = {
            "records": [{"fields": record} for record in batch],
            "performUpsert": {
                "fieldsToMergeOn": ["Product Naam"]
            }
        }

        response = requests.patch(url, headers=AIRTABLE_HEADERS, json=payload)

        if response.status_code == 200:
            result = response.json()
            success_count += len(result.get("records", []))

            # Show sample
            if i == 0 and len(batch) > 0:
                print(f"\n  Top 5 products by usage:")
                for j, record in enumerate(batch[:5], 1):
                    name = record.get("Product Naam", "?")
                    freq = record.get("Gebruik Frequentie", 0)
                    print(f"    {j}. {name} (used {freq}x)")

            print(f"  Batch {i // batch_size + 1}: OK")
        else:
            print(f"  Batch {i // batch_size + 1}: FAILED ({response.status_code})")

        time.sleep(0.3)

    print(f"\n[OK] {success_count} products added to catalog")
    return success_count


def main():
    """Main extraction process."""

    print("="*70)
    print("EXTRACTING PRODUCT CATALOG FROM OFFORTE PROPOSALS")
    print("="*70)

    # Fetch proposals
    proposals = fetch_won_proposals(limit=10)

    if not proposals:
        print("[FAIL] No proposals found")
        return

    # Extract products
    product_stats = extract_products_from_proposals(proposals)

    if not product_stats:
        print("[FAIL] No products found")
        return

    # Create catalog records
    catalog_records = create_catalog_records(product_stats)

    # Upsert to Airtable
    success = upsert_to_catalog(catalog_records)

    print("\n" + "="*70)
    print("EXTRACTION COMPLETE")
    print(f"  Unique products found: {len(catalog_records)}")
    print(f"  Successfully added: {success}")
    print("\n  Next: Add cost prices manually or match with STB-Inkoop data")
    print("="*70)


if __name__ == "__main__":
    main()
