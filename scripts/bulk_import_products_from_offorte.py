#!/usr/bin/env python3
"""
Bulk import products from ALL Offorte proposals with pagination.

Fetches all proposals, extracts unique products, calculates usage stats,
and imports to Product Catalogus.
"""

import requests
import time
from collections import defaultdict
from backend.core.settings import settings

# Offorte API
OFFORTE_API_KEY = settings.offorte_api_key
OFFORTE_BASE_URL = settings.offorte_base_url

# Airtable
AIRTABLE_API_KEY = settings.airtable_api_key
SALES_BASE_ID = settings.airtable_base_stb_sales

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}


def fetch_all_proposals():
    """Fetch ALL won proposals from Offorte with pagination."""

    all_proposals = []
    page = 1
    per_page = 50

    print("Fetching ALL won proposals from Offorte API...")
    print("This may take a while...\n")

    while True:
        url = f"{OFFORTE_BASE_URL}/proposals/won/"
        params = {
            "api_key": OFFORTE_API_KEY,
            "page": page,
            "per_page": per_page,
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code in [200, 201]:
                proposals = response.json()

                # Handle both list and dict response
                if isinstance(proposals, dict):
                    proposals = proposals.get('data', [])

                if not proposals or len(proposals) == 0:
                    break  # No more proposals

                all_proposals.extend(proposals)
                print(f"  Page {page}: Fetched {len(proposals)} proposals (Total: {len(all_proposals)})")

                # Check if we got less than per_page (last page)
                if len(proposals) < per_page:
                    break

                page += 1
                time.sleep(0.3)  # Rate limit
            else:
                print(f"  [WARN] Page {page} failed: {response.status_code}")
                break

        except Exception as e:
            print(f"  [ERROR] Failed to fetch page {page}: {e}")
            break

    print(f"\n[OK] Fetched {len(all_proposals)} total won proposals")
    return all_proposals


def fetch_proposal_details(proposal_id):
    """Fetch detailed proposal data including pricetables."""

    url = f"{OFFORTE_BASE_URL}/proposals/{proposal_id}/details"
    params = {"api_key": OFFORTE_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code in [200, 201]:
            return response.json()
    except:
        pass

    return None


def extract_products_from_proposals(proposals):
    """Extract all unique products from proposals."""

    product_stats = defaultdict(lambda: {
        "count": 0,
        "total_value": 0.0,
        "last_used": None,
        "categories": set(),
        "unit_prices": [],
    })

    print("\nExtracting products from proposals (fetching details for each)...")

    for idx, proposal in enumerate(proposals, 1):
        proposal_id = proposal.get("id")

        # Show progress every 5 proposals
        if idx % 5 == 0:
            print(f"  Processed {idx}/{len(proposals)} proposals...")

        # Fetch full details to get pricetables
        proposal_details = fetch_proposal_details(proposal_id)
        if not proposal_details:
            continue

        # Get pricetables from details
        pricetables = proposal_details.get("pricetables", [])

        # Get proposal date
        won_at = proposal.get("won_at")
        created_at = proposal.get("created_at")
        proposal_date = won_at or created_at

        for pricetable in pricetables:
            rows = pricetable.get("rows", [])

            for row in rows:
                product_name = row.get("description", "").strip()

                # Skip empty or very short names
                if not product_name or len(product_name) < 3:
                    continue

                # Skip common non-product entries
                if product_name.lower() in ["subtotaal", "totaal", "korting", "toeslag"]:
                    continue

                # Update stats
                stats = product_stats[product_name]
                stats["count"] += 1

                # Track value
                price_total = float(row.get("price_total", 0) or 0)
                stats["total_value"] += price_total

                # Track unit price if available
                unit_price = float(row.get("price", 0) or 0)
                if unit_price > 0:
                    stats["unit_prices"].append(unit_price)

                # Update last used date
                if proposal_date:
                    date_str = proposal_date.split("T")[0]
                    if not stats["last_used"] or date_str > stats["last_used"]:
                        stats["last_used"] = date_str

                # Categorize product
                name_lower = product_name.lower()
                if any(word in name_lower for word in ["hordeur", "hor", "screen"]):
                    stats["categories"].add("Hordeur")
                elif any(word in name_lower for word in ["glas", "hr++", "hr+++", "isolatie"]):
                    stats["categories"].add("Glas")
                elif any(word in name_lower for word in ["beslag", "handvat", "slot", "sluiting"]):
                    stats["categories"].add("Beslag")
                elif any(word in name_lower for word in ["profiel", "pvc", "kunststof"]):
                    stats["categories"].add("Profiel")
                elif any(word in name_lower for word in ["dorpel", "drempel"]):
                    stats["categories"].add("Onderdeel")
                elif any(word in name_lower for word in ["kit", "afdicht"]):
                    stats["categories"].add("Onderdeel")
                else:
                    stats["categories"].add("Overig")

    print(f"\n[OK] Extracted {len(product_stats)} unique products")
    return product_stats


def create_catalog_records(product_stats, min_usage=1):
    """Convert product stats to catalog records, filtering by minimum usage."""

    catalog_records = []

    for product_name, stats in product_stats.items():
        # Filter out rarely used products
        if stats["count"] < min_usage:
            continue

        # Determine category (most common)
        category = list(stats["categories"])[0] if stats["categories"] else "Overig"

        # Calculate average unit price if available
        avg_unit_price = None
        if stats["unit_prices"]:
            avg_unit_price = sum(stats["unit_prices"]) / len(stats["unit_prices"])

        # Generate Product ID from name
        product_id = (product_name
                      .upper()
                      .replace(" ", "-")
                      .replace("/", "-")
                      .replace("(", "")
                      .replace(")", "")
                      [:50])

        # Determine unit
        name_lower = product_name.lower()
        if "m2" in name_lower or "m²" in name_lower:
            unit = "m²"
        elif "m1" in name_lower or "meter" in name_lower:
            unit = "m¹"
        elif "set" in name_lower:
            unit = "Set"
        else:
            unit = "Stuk"

        catalog_record = {
            "Product Naam": product_name,
            "Product ID": product_id,
            "Categorie": category,
            "Eenheid": unit,
            "Actief": True,
            "Bron": "Offorte",
            "Laatst Gebruikt": stats["last_used"],
            "Gebruik Frequentie": stats["count"],
            "Matching Keywords": product_name.lower(),
        }

        # Add average price if available (as suggestion for cost price)
        if avg_unit_price and avg_unit_price > 0:
            catalog_record["Notities"] = f"Gemiddelde verkoopprijs: EUR {avg_unit_price:.2f} per {unit}"

        # Remove None values
        catalog_record = {k: v for k, v in catalog_record.items() if v is not None}

        catalog_records.append(catalog_record)

    # Sort by usage frequency (most used first)
    catalog_records.sort(key=lambda x: x.get("Gebruik Frequentie", 0), reverse=True)

    return catalog_records


def upsert_to_catalog(records, batch_size=10):
    """Upsert records to Product Catalogus in batches."""

    url = f"https://api.airtable.com/v0/{SALES_BASE_ID}/Product Catalogus"

    print(f"\nImporting {len(records)} products to Product Catalogus...")

    success_count = 0
    fail_count = 0

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

            # Show top products from first batch
            if i == 0:
                print(f"\n  TOP 10 MOST USED PRODUCTS:")
                for j, record in enumerate(batch[:10], 1):
                    name = record.get("Product Naam", "?")
                    freq = record.get("Gebruik Frequentie", 0)
                    cat = record.get("Categorie", "?")
                    print(f"    {j:2d}. {name[:50]:<50} ({freq:3d}x, {cat})")

            print(f"  Batch {i // batch_size + 1}/{(len(records) - 1) // batch_size + 1}: {len(result.get('records', []))} products")
        else:
            fail_count += len(batch)
            print(f"  Batch {i // batch_size + 1} FAILED: {response.status_code}")

        time.sleep(0.3)  # Rate limit

    print(f"\n[SUMMARY] {success_count} succeeded, {fail_count} failed")
    return success_count, fail_count


def main():
    """Main bulk import process."""

    print("="*70)
    print("BULK IMPORT PRODUCTS FROM ALL OFFORTE PROPOSALS")
    print("="*70)

    # Step 1: Fetch ALL proposals
    proposals = fetch_all_proposals()

    if not proposals:
        print("[FAIL] No proposals fetched")
        return

    # Step 2: Extract products
    product_stats = extract_products_from_proposals(proposals)

    if not product_stats:
        print("[FAIL] No products found")
        return

    # Step 3: Create catalog records (min 2 uses to filter noise)
    print(f"\nCreating catalog records (filtering products used < 2 times)...")
    catalog_records = create_catalog_records(product_stats, min_usage=2)

    print(f"[OK] {len(catalog_records)} products after filtering")

    # Show statistics
    categories = defaultdict(int)
    for record in catalog_records:
        categories[record.get("Categorie", "Unknown")] += 1

    print(f"\nPRODUCTS BY CATEGORY:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat}: {count} products")

    # Step 4: Import to Airtable
    if catalog_records:
        success, fail = upsert_to_catalog(catalog_records)

        print("\n" + "="*70)
        print("BULK IMPORT COMPLETE")
        print(f"  Total proposals analyzed: {len(proposals)}")
        print(f"  Unique products found: {len(product_stats)}")
        print(f"  Products imported (used 2+ times): {len(catalog_records)}")
        print(f"  Successfully added: {success}")
        print(f"  Failed: {fail}")
        print("\n  Next: Review products in Airtable and add cost prices")
        print("="*70)


if __name__ == "__main__":
    main()
