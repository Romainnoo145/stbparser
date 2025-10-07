#!/usr/bin/env python3
"""Extract products from the example JSON file to test the extraction logic."""

from backend.core.settings import settings
import json
import re
from html import unescape
from collections import defaultdict
import requests

# Airtable config
# Airtable config - using settings
SALES_BASE_ID = "app9mz6mT0zk8XRGm"

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {settings.airtable_api_key}",
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
    """Extract product names from HTML content."""
    if not html_content:
        return []

    products = []

    # Extract list items (usually subproducts)
    li_items = re.findall(r'<li[^>]*>(.*?)</li>', html_content, re.DOTALL | re.IGNORECASE)
    for item in li_items:
        clean_text = strip_html(item)
        if clean_text and len(clean_text) > 2:
            products.append(clean_text)

    # Extract paragraphs (main product)
    if not li_items:
        p_items = re.findall(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL | re.IGNORECASE)
        for item in p_items:
            clean_text = strip_html(item)
            # Skip non-products
            if clean_text and len(clean_text) > 2:
                if not any(skip in clean_text.lower() for skip in ['korting', 'inclusief', 'totaal', '*']):
                    products.append(clean_text)

    return products


# Load example JSON
print("Loading example proposal JSON...")
with open('docs/offorte_proposal_example.json', 'r', encoding='utf-8') as f:
    proposal = json.load(f)

print(f"Proposal ID: {proposal.get('id')}")
print(f"Proposal Name: {proposal.get('name')}\n")

# Extract products
product_list = []

pricetables = proposal.get('content', {}).get('pricetables', [])
print(f"Found {len(pricetables)} pricetables\n")

for pt_idx, pricetable in enumerate(pricetables, 1):
    print(f"Pricetable {pt_idx}:")
    rows = pricetable.get('rows', [])

    for row_idx, row in enumerate(rows, 1):
        html_content = row.get('content', '')
        price = row.get('price', 0)

        # Extract product names
        product_names = extract_product_names_from_html(html_content)

        if product_names:
            print(f"  Row {row_idx} (EUR {price}):")
            for product_name in product_names:
                print(f"    - {product_name}")
                product_list.append({
                    "name": product_name,
                    "price": price,
                    "row_idx": row_idx
                })
        else:
            # Show raw HTML if no products found
            preview = strip_html(html_content)[:60]
            if preview:
                print(f"  Row {row_idx}: {preview}...")

    print()

print(f"\n{'='*70}")
print(f"TOTAL UNIQUE PRODUCTS FOUND: {len(set(p['name'] for p in product_list))}")
print(f"{'='*70}\n")

# Show unique products
unique_products = {}
for p in product_list:
    name = p['name']
    if name not in unique_products:
        unique_products[name] = {"count": 0, "total_price": 0}
    unique_products[name]["count"] += 1
    unique_products[name]["total_price"] += p['price']

print("UNIQUE PRODUCTS:")
for idx, (name, stats) in enumerate(sorted(unique_products.items(), key=lambda x: x[1]["count"], reverse=True), 1):
    print(f"  {idx:2d}. {name[:60]:<60} ({stats['count']}x)")

print(f"\nThese are the REAL products we should import to Product Catalogus!")
