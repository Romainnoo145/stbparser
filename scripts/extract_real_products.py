#!/usr/bin/env python3
"""
Extract REAL products from Offorte proposals by parsing HTML content in rows.

Products are in the 'content' field as HTML, not 'description'.
"""

import requests
import time
import re
from html import unescape
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


def strip_html(html_content):
    """Strip HTML tags and extract clean text."""
    if not html_content:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)

    # Unescape HTML entities
    text = unescape(text)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def extract_product_names_from_html(html_content):
    """Extract product names from HTML content (handles lists and paragraphs)."""
    if not html_content:
        return []

    products = []

    # Extract list items (usually subproducts)
    li_items = re.findall(r'<li[^>]*>(.*?)</li>', html_content, re.DOTALL | re.IGNORECASE)
    for item in li_items:
        clean_text = strip_html(item)
        if clean_text and len(clean_text) > 2:
            products.append(clean_text)

    # Extract paragraphs (usually main product)
    if not li_items:  # Only if no list items (avoid duplicates)
        p_items = re.findall(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL | re.IGNORECASE)
        for item in p_items:
            clean_text = strip_html(item)
            # Skip obvious non-products
            if clean_text and len(clean_text) > 2:
                if not any(skip in clean_text.lower() for skip in ['korting', 'inclusief', 'totaal', '*']):
                    products.append(clean_text)

    return products


def fetch_won_proposals(limit=50):
    """Fetch won proposals from Offorte."""

    url = f"{OFFORTE_BASE_URL}/proposals/won/"
    params = {
        "api_key": OFFORTE_API_KEY,
        "per_page": limit,
    }

    print(f"Fetching {limit} won proposals from Offorte...")

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code in [200, 201]:
            proposals = response.json()

            # Handle both list and dict response
            if isinstance(proposals, dict):
                proposals = proposals.get('data', [])

            print(f"[OK] Fetched {len(proposals)} proposals")
            return proposals
    except Exception as e:
        print(f"[ERROR] Failed to fetch proposals: {e}")

    return []


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


def extract_products_from_proposals(proposals, max_proposals=20):
    """Extract all unique products from proposals."""

    product_stats = defaultdict(lambda: {
        "count": 0,
        "total_value": 0.0,
        "last_used": None,
        "categories": set(),
    })

    print(f"\nExtracting products from {min(len(proposals), max_proposals)} proposals...")

    for idx, proposal in enumerate(proposals[:max_proposals], 1):
        proposal_id = proposal.get("id")

        print(f"  [{idx}/{min(len(proposals), max_proposals)}] Proposal {proposal_id}...", end=" ")

        # Fetch details
        details = fetch_proposal_details(proposal_id)
        if not details:
            print("SKIP (no details)")
            continue

        pricetables = details.get("pricetables", [])
        won_at = proposal.get("won_at", "")
        proposal_date = won_at.split("T")[0] if won_at else None

        products_found = 0

        for pricetable in pricetables:
            rows = pricetable.get("rows", [])

            for row in rows:
                # Get HTML content
                html_content = row.get("content", "")

                # Extract product names from HTML
                product_names = extract_product_names_from_html(html_content)

                for product_name in product_names:
                    if len(product_name) < 3:
                        continue

                    # Update stats
                    stats = product_stats[product_name]
                    stats["count"] += 1
                    products_found += 1

                    # Track value
                    price = float(row.get("price", 0) or 0)
                    stats["total_value"] += price

                    # Update last used
                    if proposal_date:
                        if not stats["last_used"] or proposal_date > stats["last_used"]:
                            stats["last_used"] = proposal_date

                    # Categorize
                    name_lower = product_name.lower()
                    if any(word in name_lower for word in ["hordeur", "hor", "screen", "plisse"]):
                        stats["categories"].add("Hordeur")
                    elif any(word in name_lower for word in ["glas", "hr++", "hr+++", "triple", "dubbel", "isolatie"]):
                        stats["categories"].add("Glas")
                    elif any(word in name_lower for word in ["beslag", "handvat", "slot", "sluiting", "cilinder", "hang"]):
                        stats["categories"].add("Beslag")
                    elif any(word in name_lower for word in ["profiel", "pvc", "kunststof"]):
                        stats["categories"].add("Profiel")
                    elif any(word in name_lower for word in ["dorpel", "drempel", "hardsteen", "onderdorpel"]):
                        stats["categories"].add("Onderdeel")
                    elif any(word in name_lower for word in ["kit", "afdicht"]):
                        stats["categories"].add("Onderdeel")
                    elif any(word in name_lower for word in ["keylite", "velux", "dakraam"]):
                        stats["categories"].add("Overig")
                    else:
                        stats["categories"].add("Overig")

        print(f"Found {products_found} products")
        time.sleep(0.2)  # Rate limit

    print(f"\n[OK] Extracted {len(product_stats)} unique products")
    return product_stats


def create_catalog_records(product_stats, min_usage=2):
    """Convert product stats to catalog records."""

    catalog_records = []

    for product_name, stats in product_stats.items():
        # Filter by minimum usage
        if stats["count"] < min_usage:
            continue

        # Determine category
        category = list(stats["categories"])[0] if stats["categories"] else "Overig"

        # Generate Product ID
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

        # Remove None values
        catalog_record = {k: v for k, v in catalog_record.items() if v is not None}

        catalog_records.append(catalog_record)

    # Sort by frequency
    catalog_records.sort(key=lambda x: x.get("Gebruik Frequentie", 0), reverse=True)

    return catalog_records


def upsert_to_catalog(records, batch_size=10):
    """Upsert records to Product Catalogus."""

    url = f"https://api.airtable.com/v0/{SALES_BASE_ID}/Product Catalogus"

    print(f"\nImporting {len(records)} products to Product Catalogus...")

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

            # Show top 10 from first batch
            if i == 0:
                print(f"\n  TOP 10 MOST USED PRODUCTS:")
                for j, record in enumerate(batch[:10], 1):
                    name = record.get("Product Naam", "?")
                    freq = record.get("Gebruik Frequentie", 0)
                    cat = record.get("Categorie", "?")
                    print(f"    {j:2d}. {name[:55]:<55} ({freq:2d}x, {cat})")

            print(f"  Batch {i // batch_size + 1}: OK")
        else:
            print(f"  Batch {i // batch_size + 1}: FAILED ({response.status_code})")

        time.sleep(0.3)

    print(f"\n[OK] {success_count} products imported")
    return success_count


def main():
    """Main extraction process."""

    print("="*70)
    print("EXTRACTING REAL PRODUCTS FROM OFFORTE PROPOSALS")
    print("="*70)

    # Step 1: Fetch proposals
    proposals = fetch_won_proposals(limit=50)

    if not proposals:
        print("[FAIL] No proposals found")
        return

    # Step 2: Extract products (limit to first 20 to avoid timeout)
    product_stats = extract_products_from_proposals(proposals, max_proposals=20)

    if not product_stats:
        print("[FAIL] No products found")
        return

    # Step 3: Create catalog records
    catalog_records = create_catalog_records(product_stats, min_usage=2)

    print(f"\n[OK] {len(catalog_records)} products after filtering (used 2+ times)")

    # Show category breakdown
    categories = defaultdict(int)
    for record in catalog_records:
        categories[record.get("Categorie", "Unknown")] += 1

    print(f"\nPRODUCTS BY CATEGORY:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat}: {count} products")

    # Step 4: Import to Airtable
    if catalog_records:
        success = upsert_to_catalog(catalog_records)

        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print(f"  Proposals analyzed: 20")
        print(f"  Unique products found: {len(product_stats)}")
        print(f"  Products imported (used 2+ times): {len(catalog_records)}")
        print(f"  Successfully added: {success}")
        print("\n  Next: Add cost prices in Airtable or match with STB-Inkoop")
        print("="*70)


if __name__ == "__main__":
    main()
