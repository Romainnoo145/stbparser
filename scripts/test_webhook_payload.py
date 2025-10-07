#!/usr/bin/env python3
"""Test transformation with simulated webhook payload."""

import json
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records

# Simulated webhook payload (smaller version for testing)
webhook_payload = {
    "type": "proposal_won",
    "date_created": "2025-10-07T18:46:50.000000Z",
    "data": {
        "id": "309107",
        "proposal_nr": "2754",
        "price_total_original": "11366.60",
        "date_won": "2025-10-07T18:46:50.000000Z",
        "contact": {
            "name": "Marijn Janssen",
            "fullname": "Marijn Janssen",
            "street": "Vinkepas 5",
            "zipcode": "5975 PN",
            "city": "Sevenum",
            "phone": "06-31743776",
            "email": "marijnjanssen87@gmail.com"
        },
        "content": {
            "pricetables": [
                {
                    "subtotal": 3427,
                    "total": 4146.67,
                    "rows": [
                        {
                            "content": "<p>Voorzetrolluik SKE (2450x1760mm)</p>",
                            "price": 555,
                            "quantity": 1,
                            "subtotal": 555,
                            "type": "price"
                        },
                        {
                            "content": "<p>Meerprijs IO motor</p><p><em>Elektrisch bediend</em></p>",
                            "price": 195,
                            "quantity": 3,
                            "subtotal": 585,
                            "type": "price"
                        }
                    ]
                }
            ]
        }
    }
}

print("="*80)
print("TESTING WEBHOOK PAYLOAD TRANSFORMATION")
print("="*80)

# Transform using the webhook payload data
proposal_data = webhook_payload['data']

try:
    all_records = transform_proposal_to_all_records(proposal_data)

    print(f"\nTransformation Results:")
    print(f"  Klantenportaal: {len(all_records['klantenportaal'])} record(s)")
    print(f"  Elementen Overzicht: {len(all_records['elementen_overzicht'])} record(s)")
    print(f"  Element Specificaties: {len(all_records['element_specificaties'])} record(s)")
    print(f"  Subproducten: {len(all_records['subproducten'])} record(s)")
    print(f"  Nacalculatie: {len(all_records['nacalculatie'])} record(s)")

    print("\n" + "="*80)
    print("KLANTENPORTAAL")
    print("="*80)
    print(json.dumps(all_records['klantenportaal'][0], indent=2))

    if all_records['elementen_overzicht']:
        print("\n" + "="*80)
        print("FIRST ELEMENT")
        print("="*80)
        print(json.dumps(all_records['elementen_overzicht'][0], indent=2))

    print("\n[OK] Transformation successful!")

except Exception as e:
    print(f"\n[FAIL] Transformation failed: {e}")
    import traceback
    traceback.print_exc()
