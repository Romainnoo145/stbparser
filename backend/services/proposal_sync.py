"""
Direct proposal sync service - no AI agent needed.

Handles complete Offorte -> Airtable sync deterministically.
"""

import requests
from typing import Dict, Any
from urllib.parse import quote
from loguru import logger

from backend.core.settings import settings
from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records
from backend.services.airtable_sync import AirtableSync


class ProposalSyncService:
    """Direct sync service for Offorte proposals to Airtable."""

    def __init__(self):
        """Initialize sync service."""
        self.offorte_api_key = settings.offorte_api_key
        self.offorte_account = quote(settings.offorte_account_name)
        self.base_url = f"https://connect.offorte.com/api/v2/{self.offorte_account}"
        self.airtable_sync = AirtableSync()

    def fetch_proposal(self, proposal_id: int) -> Dict[str, Any]:
        """
        Fetch complete proposal data from Offorte API.

        Args:
            proposal_id: Offorte proposal ID

        Returns:
            Complete proposal data

        Raises:
            Exception if fetch fails
        """
        url = f"{self.base_url}/proposals/{proposal_id}/details"
        params = {"api_key": self.offorte_api_key}

        logger.info(f"Fetching proposal {proposal_id} from Offorte...")

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            proposal_data = response.json()
            logger.info(f"Successfully fetched proposal {proposal_id}")

            # Log summary
            customer = proposal_data.get('customer', {})
            pricetables = proposal_data.get('pricetables', [])
            logger.info(
                f"Proposal {proposal_id}: "
                f"customer={customer.get('company_name') or customer.get('full_name')}, "
                f"pricetables={len(pricetables)}"
            )

            return proposal_data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching proposal {proposal_id}: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"Error fetching proposal {proposal_id}: {e}")
            raise

    def sync_proposal(self, proposal_id: int) -> Dict[str, Any]:
        """
        Complete sync of proposal from Offorte to Airtable.

        Steps:
        1. Fetch proposal from Offorte
        2. Transform to Airtable records
        3. Sync to all STB-SALES tables

        Args:
            proposal_id: Offorte proposal ID

        Returns:
            Sync result with statistics
        """
        result = {
            "success": False,
            "proposal_id": proposal_id,
            "steps": {},
            "errors": []
        }

        try:
            # Step 1: Fetch from Offorte
            logger.info(f"Step 1: Fetching proposal {proposal_id}")
            try:
                proposal_data = self.fetch_proposal(proposal_id)
                result["steps"]["fetch"] = "success"
            except Exception as e:
                error_msg = f"Failed to fetch proposal: {e}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["steps"]["fetch"] = "failed"
                return result

            # Step 2: Transform to Airtable records
            logger.info(f"Step 2: Transforming proposal {proposal_id}")
            try:
                all_records = transform_proposal_to_all_records(proposal_data)
                result["steps"]["transform"] = "success"
                result["record_counts"] = {
                    table: len(records)
                    for table, records in all_records.items()
                }
                logger.info(f"Transformation created {sum(result['record_counts'].values())} total records")
            except Exception as e:
                error_msg = f"Failed to transform proposal: {e}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["steps"]["transform"] = "failed"
                return result

            # Step 3: Sync to Airtable
            logger.info(f"Step 3: Syncing to Airtable")
            try:
                sync_results = self.airtable_sync.sync_proposal_records(all_records)
                result["steps"]["sync"] = "success"
                result["sync_results"] = sync_results

                # Check for any failures
                total_failed = sum(
                    stats.get("failed", 0)
                    for stats in sync_results.values()
                )

                if total_failed > 0:
                    result["errors"].append(f"{total_failed} records failed to sync")
                    logger.warning(f"Sync completed with {total_failed} failures")
                else:
                    logger.info(f"All records synced successfully")
                    result["success"] = True

            except Exception as e:
                error_msg = f"Failed to sync to Airtable: {e}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["steps"]["sync"] = "failed"
                return result

        except Exception as e:
            error_msg = f"Unexpected error during sync: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result


# Global instance
sync_service = ProposalSyncService()


async def process_proposal_sync(proposal_id: int, job_id: str = None) -> Dict[str, Any]:
    """
    Main entry point for proposal sync (async wrapper for compatibility).

    Args:
        proposal_id: Offorte proposal ID
        job_id: Optional job ID for tracking

    Returns:
        Sync result dictionary
    """
    if job_id:
        logger.info(f"Processing sync job {job_id} for proposal {proposal_id}")
    else:
        logger.info(f"Processing proposal {proposal_id}")

    return sync_service.sync_proposal(proposal_id)
