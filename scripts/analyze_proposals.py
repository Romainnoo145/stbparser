#!/usr/bin/env python3
"""Analyze multiple Offorte proposals to understand data structure."""

import requests
import json
from time import sleep

api_key = "H7EhsUhJ4kEQFM7K7PJJOAgW7WxOpcXJ"
base_url = "https://connect.offorte.com/api/v2/stb-kozijnen"

# Top 10 largest proposals
proposal_ids = [288976, 308545, 305741, 284903, 291725, 291966, 291913, 292076, 277120, 304743]

findings = {
    "total_analyzed": 0,
    "has_pricetables": 0,
    "total_rows": 0,
    "row_types": set(),
    "sample_rows": [],
    "field_patterns": {}
}

for proposal_id in proposal_ids:
    print(f"Analyzing proposal {proposal_id}...")

    try:
        response = requests.get(
            f"{base_url}/proposals/{proposal_id}/details?api_key={api_key}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            findings["total_analyzed"] += 1

            # Analyze content structure
            if "content" in data and "pricetables" in data["content"]:
                findings["has_pricetables"] += 1

                for table in data["content"]["pricetables"]:
                    if "rows" in table:
                        findings["total_rows"] += len(table["rows"])

                        for row in table["rows"]:
                            findings["row_types"].add(row.get("type", "unknown"))

                            # Collect sample row for analysis
                            if len(findings["sample_rows"]) < 20:
                                findings["sample_rows"].append({
                                    "proposal_id": proposal_id,
                                    "type": row.get("type"),
                                    "content_preview": row.get("content", "")[:200],
                                    "price": row.get("price"),
                                    "quantity": row.get("quantity"),
                                    "keys": list(row.keys())
                                })

            # Check for custom fields
            if data.get("custom_fields"):
                findings["field_patterns"]["custom_fields"] = data["custom_fields"]

            # Save first 3 full proposals for detailed review
            if findings["total_analyzed"] <= 3:
                with open(f'/tmp/proposal_{proposal_id}.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"  Saved full data to /tmp/proposal_{proposal_id}.json")

        else:
            print(f"  Failed: {response.status_code}")

        sleep(0.5)  # Rate limiting

    except Exception as e:
        print(f"  Error: {e}")

# Print summary
print("\n" + "="*80)
print("ANALYSIS SUMMARY")
print("="*80)
print(f"Total proposals analyzed: {findings['total_analyzed']}")
print(f"Proposals with pricetables: {findings['has_pricetables']}")
print(f"Total price rows found: {findings['total_rows']}")
print(f"Row types found: {findings['row_types']}")

print("\n--- SAMPLE ROWS ---")
for i, sample in enumerate(findings['sample_rows'][:10], 1):
    print(f"\nSample {i} (Proposal {sample['proposal_id']}):")
    print(f"  Type: {sample['type']}")
    print(f"  Price: {sample['price']}")
    print(f"  Quantity: {sample['quantity']}")
    print(f"  Content preview: {sample['content_preview']}")
    print(f"  All keys: {sample['keys']}")

# Save findings
with open('/tmp/offorte_analysis.json', 'w') as f:
    # Convert set to list for JSON serialization
    findings['row_types'] = list(findings['row_types'])
    json.dump(findings, f, indent=2)

print("\n\nFull analysis saved to: /tmp/offorte_analysis.json")
