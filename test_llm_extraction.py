#!/usr/bin/env python3
"""
Test LLM-based spec extraction with example Offorte data.
"""

import json
import sys
from pathlib import Path
from pprint import pprint

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.transformers.llm_spec_extractor import extract_specs_with_llm
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records


def test_llm_extraction():
    """Test LLM extraction with example proposal."""

    # Use example proposal
    example_file = Path(__file__).parent / "docs" / "offorte_proposal_example.json"

    if not example_file.exists():
        print(f"❌ Example file not found: {example_file}")
        return

    print(f"📄 Loading example proposal from {example_file}")
    with open(example_file, 'r') as f:
        proposal_data = json.load(f)

    proposal_id = proposal_data.get('id')
    customer_name = proposal_data.get('contact', {}).get('fullname', 'Unknown')

    print(f"\n{'='*80}")
    print(f"Testing LLM Extraction")
    print(f"{'='*80}")
    print(f"📋 Proposal ID: {proposal_id}")
    print(f"👤 Customer: {customer_name}")

    # Get pricetables
    content = proposal_data.get('content', {})
    pricetables = content.get('pricetables', [])

    print(f"📦 Pricetables: {len(pricetables)}\n")

    # Test LLM extraction on first pricetable
    if pricetables:
        print(f"\n{'─'*80}")
        print(f"Testing LLM Extraction on First Pricetable")
        print(f"{'─'*80}\n")

        pricetable = pricetables[0]
        rows = pricetable.get('rows', [])

        print(f"Rows in pricetable: {len(rows)}")

        # Show raw HTML
        if rows:
            main_row = rows[0]
            html = main_row.get('content', '')
            print(f"\n📄 Main product HTML (first 300 chars):")
            print(html[:300] + "..." if len(html) > 300 else html)

        # Extract specs using LLM
        print(f"\n🤖 Extracting specs with LLM...")
        try:
            specs = extract_specs_with_llm(pricetable, element_type="Deur")

            print(f"\n✅ LLM Extraction Results:")
            print(f"{'─'*80}")

            # Count filled vs N.v.t
            filled = 0
            nvt = 0

            for key, value in sorted(specs.items()):
                if value and str(value) != 'N.v.t':
                    filled += 1
                    val_str = str(value)
                    if len(val_str) > 60:
                        val_str = val_str[:60] + "..."
                    print(f"  ✅ {key}: {val_str}")
                else:
                    nvt += 1

            print(f"\n📊 Stats:")
            print(f"  • Filled fields: {filled}")
            print(f"  • N.v.t fields: {nvt}")
            print(f"  • Coverage: {filled}/{filled+nvt} ({filled*100//(filled+nvt)}%)")

        except Exception as e:
            print(f"❌ LLM extraction failed: {e}")
            import traceback
            traceback.print_exc()

    # Test full transformation
    print(f"\n\n{'='*80}")
    print("Full Transformation Test (with LLM)")
    print(f"{'='*80}\n")

    try:
        all_records = transform_proposal_to_all_records(proposal_data)

        print(f"✅ Klantenportaal: {len(all_records.get('klantenportaal', []))} records")
        print(f"✅ Elementen Overzicht: {len(all_records.get('elementen_overzicht', []))} records")
        print(f"✅ Element Specificaties: {len(all_records.get('element_specificaties', []))} records")
        print(f"✅ Subproducten: {len(all_records.get('subproducten', []))} records")

        # Show first element specs in detail
        specs_records = all_records.get('element_specificaties', [])
        if specs_records:
            print(f"\n📋 First Element Specificaties Record:")
            print(f"{'─'*80}")
            first_spec = specs_records[0]

            filled = 0
            nvt = 0

            for key, value in sorted(first_spec.items()):
                if value:
                    val_str = str(value)
                    if val_str == 'N.v.t':
                        nvt += 1
                    else:
                        filled += 1
                        if len(val_str) > 60:
                            val_str = val_str[:60] + "..."
                        print(f"  {key}: {val_str}")

            print(f"\n📊 Field Stats:")
            print(f"  • Filled: {filled} fields")
            print(f"  • N.v.t: {nvt} fields")
            print(f"  • Total: {filled + nvt} fields")

    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"🧪 LLM-Based Spec Extraction Test")
    print(f"{'='*80}\n")

    test_llm_extraction()

    print(f"\n{'='*80}")
    print("✅ Testing Complete")
    print(f"{'='*80}\n")
