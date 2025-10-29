#!/usr/bin/env python3
"""
Test script to sync parsed proposal data to actual Airtable tables.
This will create real records in your Airtable bases.
"""

import json
import sys
from pathlib import Path
from pprint import pprint

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records
from backend.services.airtable_sync import AirtableSync
from loguru import logger


def sync_proposal_to_airtable(json_path: str, dry_run: bool = False):
    """
    Transform and sync a proposal to Airtable.

    Args:
        json_path: Path to proposal JSON file
        dry_run: If True, only show what would be synced without actually syncing
    """
    print(f"\n{'='*80}")
    print(f"🔄 Syncing: {json_path}")
    print(f"{'='*80}\n")

    # Load proposal data
    with open(json_path, 'r') as f:
        proposal_data = json.load(f)

    proposal_id = proposal_data.get('id')
    customer_name = proposal_data.get('contact', {}).get('fullname', 'Unknown')

    print(f"📋 Proposal ID: {proposal_id}")
    print(f"👤 Customer: {customer_name}")

    # Transform to Airtable records
    print(f"\n🔄 Transforming proposal data...")
    all_records = transform_proposal_to_all_records(proposal_data)

    # Show summary
    print(f"\n📊 Records to sync:")
    print(f"  • Klantenportaal: {len(all_records.get('klantenportaal', []))}")
    print(f"  • Elementen Overzicht: {len(all_records.get('elementen_overzicht', []))}")
    print(f"  • Element Specificaties: {len(all_records.get('element_specificaties', []))}")
    print(f"  • Subproducten: {len(all_records.get('subproducten', []))}")
    print(f"  • Nacalculatie: {len(all_records.get('nacalculatie', []))}")
    print(f"  • Inmeetplanning: {len(all_records.get('inmeetplanning', []))}")
    print(f"  • Projecten: {len(all_records.get('projecten', []))}")
    print(f"  • Facturatie: {len(all_records.get('facturatie', []))}")

    if dry_run:
        print(f"\n⚠️  DRY RUN - Not syncing to Airtable")
        print(f"\n📋 First Element Specificaties Record:")
        print(f"{'─'*80}")
        specs_records = all_records.get('element_specificaties', [])
        if specs_records:
            first_spec = specs_records[0]
            for key, value in first_spec.items():
                if value:
                    print(f"  {key}: {value}")
        return

    # Initialize sync service
    print(f"\n🚀 Starting Airtable sync...")
    sync = AirtableSync()

    # Sync order matters - Klantenportaal first, then elements, then specs
    sync_order = [
        ('klantenportaal', 'Klantenportaal'),
        ('inmeetplanning', 'Inmeetplanning'),
        ('projecten', 'Projecten'),
        ('facturatie', 'Facturatie'),
        ('elementen_overzicht', 'Elementen Overzicht'),
        ('element_specificaties', 'Element Specificaties'),
        ('subproducten', 'Subproducten'),
        ('nacalculatie', 'Nacalculatie'),
    ]

    results = {}

    for internal_name, display_name in sync_order:
        records = all_records.get(internal_name, [])
        if not records:
            continue

        print(f"\n{'─'*80}")
        print(f"📤 Syncing {display_name} ({len(records)} records)...")
        print(f"{'─'*80}")

        synced_ids = []

        for idx, record in enumerate(records, 1):
            try:
                # Show what we're syncing
                key_field = None
                if internal_name == 'klantenportaal':
                    key_field = 'Opdrachtnummer'
                elif internal_name in ['elementen_overzicht', 'element_specificaties', 'subproducten', 'nacalculatie']:
                    key_field = 'Element ID' if internal_name == 'elementen_overzicht' else 'Element ID Ref'
                elif internal_name == 'inmeetplanning':
                    key_field = 'Opdrachtnummer'
                elif internal_name == 'projecten':
                    key_field = 'Project ID'
                elif internal_name == 'facturatie':
                    key_field = 'Factuur ID'

                key_value = record.get(key_field, 'N/A') if key_field else 'N/A'

                print(f"  [{idx}/{len(records)}] {key_field}: {key_value}...", end=" ")

                record_id = sync.upsert_record(internal_name, record)

                if record_id:
                    print(f"✅ {record_id}")
                    synced_ids.append(record_id)
                else:
                    print(f"❌ Failed")

            except Exception as e:
                print(f"❌ Error: {e}")
                logger.exception(f"Failed to sync {internal_name} record")

        results[display_name] = {
            'total': len(records),
            'synced': len(synced_ids),
            'ids': synced_ids
        }

    # Summary
    print(f"\n{'='*80}")
    print(f"✅ Sync Complete")
    print(f"{'='*80}\n")

    for table_name, result in results.items():
        status = "✅" if result['synced'] == result['total'] else "⚠️"
        print(f"{status} {table_name}: {result['synced']}/{result['total']} synced")

    print(f"\n🔗 Check your Airtable bases:")
    print(f"  • STB-SALES: https://airtable.com/app9mz6mT0zk8XRGm")
    print(f"  • STB-ADMINISTRATIE: https://airtable.com/appuXCPmvIwowH78k")


if __name__ == "__main__":
    import sys

    # Check if dry run
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("🔍 Running in DRY RUN mode - no data will be written to Airtable\n")

    # Test with rolluiken data
    test_file = "/tmp/offorte_full.json"

    if Path(test_file).exists():
        sync_proposal_to_airtable(test_file, dry_run=dry_run)
    else:
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
