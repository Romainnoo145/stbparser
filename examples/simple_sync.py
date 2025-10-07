"""
Simple Sync Example

Shows how to manually sync a proposal from Offorte to Airtable using the agent.
"""

import asyncio
from backend.agent.agent import process_proposal_sync


async def main():
    """
    Example: Manually sync a single proposal by ID.
    """
    # Replace with actual proposal ID from Offorte
    proposal_id = 12345
    job_id = "manual-sync-example"

    print(f"Starting sync for proposal {proposal_id}...")

    try:
        result = await process_proposal_sync(
            proposal_id=proposal_id,
            job_id=job_id
        )

        if result.get("success"):
            print(f"✅ Sync completed successfully!")
            print(f"   Proposal: {result.get('proposal_nr')}")
            print(f"   Records created: {result.get('total_records_created')}")
            print(f"   Records updated: {result.get('total_records_updated')}")
            print(f"   Processing time: {result.get('processing_time_seconds')}s")

            print("\n📊 Table sync summary:")
            for table, stats in result.get("sync_summary", {}).items():
                print(f"   - {table}: {stats['created']} created, {stats['updated']} updated")

        else:
            print(f"❌ Sync failed!")
            for error in result.get("errors", []):
                print(f"   Error: {error}")

    except Exception as e:
        print(f"❌ Exception occurred: {e}")


if __name__ == "__main__":
    # Make sure .env is configured with:
    # - OFFORTE_API_KEY
    # - AIRTABLE_API_KEY
    # - LLM_API_KEY
    # - All base IDs

    asyncio.run(main())
