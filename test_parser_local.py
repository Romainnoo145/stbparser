#!/usr/bin/env python3
"""
Local test script for enhanced specs parser.
Tests with actual Offorte API responses without hitting Railway/Airtable.
"""

import json
import sys
from pathlib import Path
from pprint import pprint

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.transformers.specs_parser import (
    extract_specs_from_pricetable,
    extract_dimensions_from_text,
    extract_product_name_clean,
    determine_element_type_enhanced
)
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records


def test_with_file(json_path: str):
    """Test parser with a JSON file."""
    print(f"\n{'='*80}")
    print(f"Testing with: {json_path}")
    print(f"{'='*80}\n")

    with open(json_path, 'r') as f:
        proposal_data = json.load(f)

    proposal_id = proposal_data.get('id')
    customer_name = proposal_data.get('contact', {}).get('fullname', 'Unknown')

    print(f"📋 Proposal ID: {proposal_id}")
    print(f"👤 Customer: {customer_name}")

    # Get pricetables
    content = proposal_data.get('content', {})
    pricetables = content.get('pricetables', [])

    print(f"📦 Pricetables: {len(pricetables)}\n")

    # Test each pricetable
    for idx, pricetable in enumerate(pricetables):
        print(f"\n{'─'*80}")
        print(f"Pricetable {idx + 1}")
        print(f"{'─'*80}")

        rows = pricetable.get('rows', [])
        print(f"Rows: {len(rows)}")

        # Show raw HTML from first row
        if rows:
            main_row = rows[0]
            html = main_row.get('content', '')
            print(f"\n📄 Main product HTML:")
            print(html[:200] + "..." if len(html) > 200 else html)

        # Extract specs using new parser
        print(f"\n🔍 Extracted Specs:")
        specs = extract_specs_from_pricetable(pricetable)

        if not specs:
            print("  ⚠️  No specs extracted!")
        else:
            for key, value in specs.items():
                if value:  # Only show non-empty values
                    print(f"  • {key}: {value}")

    # Now test full transformation
    print(f"\n\n{'='*80}")
    print("Full Transformation Test")
    print(f"{'='*80}\n")

    try:
        all_records = transform_proposal_to_all_records(proposal_data)

        print(f"✅ Klantenportaal records: {len(all_records.get('klantenportaal', []))}")
        print(f"✅ Elementen Overzicht: {len(all_records.get('elementen_overzicht', []))}")
        print(f"✅ Element Specificaties: {len(all_records.get('element_specificaties', []))}")
        print(f"✅ Subproducten: {len(all_records.get('subproducten', []))}")
        print(f"✅ Nacalculatie: {len(all_records.get('nacalculatie', []))}")

        # Show first element specs in detail
        specs_records = all_records.get('element_specificaties', [])
        if specs_records:
            print(f"\n📋 First Element Specificaties Record:")
            print(f"{'─'*80}")
            first_spec = specs_records[0]
            for key, value in first_spec.items():
                if value:  # Only show non-empty
                    print(f"  {key}: {value}")

    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Test with all available files
    test_files = [
        "/tmp/offorte_full.json",
        "/tmp/offorte_response.json",
        "/tmp/offorte_test_ramen.json"
    ]

    for test_file in test_files:
        if Path(test_file).exists():
            test_with_file(test_file)
        else:
            print(f"⚠️  File not found: {test_file}")

    print(f"\n{'='*80}")
    print("✅ Testing Complete")
    print(f"{'='*80}\n")
