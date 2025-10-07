#!/usr/bin/env python3
"""Debug transformation output."""

import json
import redis

# Get webhook data from Redis
redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)

# Get queue length first
queue_len = redis_client.llen("sync_queue")
print(f"Queue length: {queue_len}")

if queue_len == 0:
    print("Queue is empty - webhook already processed")
    exit(0)

# Peek at first job without removing it
job_json = redis_client.lindex("sync_queue", 0)
job_data = json.loads(job_json)
raw_payload = job_data["raw_payload"]
proposal_data = raw_payload.get("data", {})

# Transform
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records
all_records = transform_proposal_to_all_records(proposal_data)

# Show one record from each failing table
print("\n" + "="*80)
print("ELEMENT SPECIFICATIES - Sample Record #1")
print("="*80)
if all_records.get("element_specificaties"):
    record = all_records["element_specificaties"][0]
    for field, value in sorted(record.items()):
        print(f"{field}: {value}")

print("\n" + "="*80)
print("SUBPRODUCTEN - Sample Record #1")
print("="*80)
if all_records.get("subproducten"):
    record = all_records["subproducten"][0]
    for field, value in sorted(record.items()):
        print(f"{field}: {value}")

print("\n" + "="*80)
print("NACALCULATIE - Sample Record #1")
print("="*80)
if all_records.get("nacalculatie"):
    record = all_records["nacalculatie"][0]
    for field, value in sorted(record.items()):
        print(f"{field}: {value}")
