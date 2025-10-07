#!/usr/bin/env python3
"""Manually sync proposal 309107 using the transformation logic."""

from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records
from backend.services.airtable_sync import AirtableSync
from backend.services.proposal_sync import sync_service
import json

print("="*80)
print("MANUAL SYNC - Proposal 309107")
print("="*80)

# Option 1: Use the sync service (will call Offorte API)
print("\nOption 1: Using sync service (calls Offorte API)...")
result = sync_service.sync_proposal(309107)

print("\nResult:")
print(json.dumps(result, indent=2))

if result.get("success"):
    print("\n[SUCCESS] Sync completed!")
    print(f"\nRecords created:")
    for table, count in result.get("record_counts", {}).items():
        print(f"  {table}: {count}")
else:
    print("\n[FAILED] Sync failed!")
    print(f"Errors: {result.get('errors')}")
