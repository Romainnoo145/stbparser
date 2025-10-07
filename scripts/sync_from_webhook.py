#!/usr/bin/env python3
"""Sync proposal from webhook payload."""

import json
import redis
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records
from backend.services.airtable_sync import AirtableSync

# Get job from Redis queue
redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
job_json = redis_client.lpop("sync_queue")

if not job_json:
    print("No jobs in queue")
    exit(0)

job_data = json.loads(job_json)
proposal_id = job_data["proposal_id"]
raw_payload = job_data["raw_payload"]

print(f"Processing proposal {proposal_id} from webhook...")
print("="*80)

# Extract proposal data from webhook
proposal_data = raw_payload.get("data", {})

# Transform
print("\nTransforming data...")
all_records = transform_proposal_to_all_records(proposal_data)

for table_name, records in all_records.items():
    print(f"  {table_name}: {len(records)} records")

# Sync to Airtable
print("\nSyncing to Airtable...")
airtable_sync = AirtableSync()
sync_results = airtable_sync.sync_proposal_records(all_records)

# Display results
print("\nSync Results:")
print("="*80)
for table_name, result in sync_results.items():
    status = "[OK]" if result["success_count"] > 0 else "[FAIL]"
    print(f"{status} {table_name}: {result['success_count']} synced, {result['error_count']} failed")

    if result["errors"]:
        for error in result["errors"][:3]:  # Show first 3 errors
            print(f"  Error: {error}")

print("="*80)
print(f"Total: {sum(r['success_count'] for r in sync_results.values())} records synced")
