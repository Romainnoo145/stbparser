"""
Agent tools for Offorte-Airtable synchronization.

Implements 6 essential tools for webhook validation, API fetching, data transformation,
and Airtable synchronization.
"""

import hashlib
import hmac
import json
import re
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import uuid4

from pydantic_ai import RunContext
from pyairtable import Api as AirtableApi
from loguru import logger

from backend.core.dependencies import AgentDependencies


# ============================================================================
# Tool 1: validate_webhook
# ============================================================================

def validate_webhook(payload: dict, signature: str, secret: str) -> Dict[str, Any]:
    """
    Validate Offorte webhook signatures for security.

    Args:
        payload: The webhook payload from Offorte
        signature: The signature header from request
        secret: Webhook secret from environment

    Returns:
        Dict with validation result
    """
    try:
        # Generate expected signature using HMAC-SHA256
        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        is_valid = hmac.compare_digest(expected_signature, signature)

        if not is_valid:
            logger.warning("Invalid webhook signature received")
            return {"valid": False, "error": "Invalid signature"}

        # Extract event details
        event_type = payload.get("type", "")
        proposal_id = payload.get("data", {}).get("id", 0)
        timestamp = payload.get("date_created", "")

        logger.info(f"Valid webhook: type={event_type}, proposal_id={proposal_id}")

        return {
            "valid": True,
            "event_type": event_type,
            "proposal_id": proposal_id,
            "timestamp": timestamp
        }

    except Exception as e:
        logger.error(f"Webhook validation failed: {e}")
        return {"valid": False, "error": str(e)}


# ============================================================================
# Tool 2: fetch_proposal_data
# ============================================================================

async def fetch_proposal_data(
    ctx: RunContext[AgentDependencies],
    proposal_id: int,
    include_content: bool = True
) -> Dict[str, Any]:
    """
    Fetch complete proposal data from Offorte API.

    Args:
        ctx: Agent run context
        proposal_id: Offorte proposal ID
        include_content: Whether to fetch detailed content

    Returns:
        Complete proposal object with nested data
    """
    deps = ctx.deps
    base_url = f"{deps.offorte_base_url}/{deps.offorte_account_name}"
    headers = {
        "Authorization": f"Bearer {deps.offorte_api_key}",
        "Content-Type": "application/json"
    }

    async def fetch_with_retry(url: str, retries: int = 3) -> dict:
        """Fetch with exponential backoff retry."""
        for attempt in range(retries):
            try:
                response = await deps.http_client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == retries - 1:
                    raise
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"Retry {attempt + 1}/{retries} after {wait_time}s: {e}")
                await asyncio.sleep(wait_time)

    try:
        # Fetch main proposal data
        logger.info(f"Fetching proposal {proposal_id}")
        proposal_url = f"{base_url}/proposals/{proposal_id}"
        proposal_data = await fetch_with_retry(proposal_url)

        # Fetch proposal content (line items)
        if include_content:
            content_url = f"{base_url}/proposals/{proposal_id}/content"
            proposal_data["content"] = await fetch_with_retry(content_url)

        # Fetch company details
        if "company_id" in proposal_data:
            company_url = f"{base_url}/companies/{proposal_data['company_id']}"
            proposal_data["company"] = await fetch_with_retry(company_url)

        # Fetch contact details
        if "contact_ids" in proposal_data and proposal_data["contact_ids"]:
            contacts = []
            for contact_id in proposal_data["contact_ids"][:5]:  # Limit to 5 contacts
                contact_url = f"{base_url}/contacts/{contact_id}"
                contacts.append(await fetch_with_retry(contact_url))
            proposal_data["contacts"] = contacts

        logger.info(f"Successfully fetched proposal {proposal_id}")
        return proposal_data

    except Exception as e:
        logger.error(f"Failed to fetch proposal {proposal_id}: {e}")
        return {"error": str(e), "proposal_id": proposal_id}


# ============================================================================
# Tool 3: parse_construction_elements
# ============================================================================

def parse_construction_elements(
    proposal_content: dict,
    proposal_nr: str
) -> List[Dict[str, Any]]:
    """
    Parse Dutch construction elements from proposal content.

    Args:
        proposal_content: The content blocks from proposal
        proposal_nr: Proposal number for element IDs

    Returns:
        List of normalized element dictionaries
    """
    elements = []
    current_brand = None
    element_index = 0

    # Element type patterns
    ELEMENT_TYPES = [
        "Draaikiep raam",
        "Vast raam",
        "Voordeur",
        "Achterdeur",
        "Tuindeur",
        "Schuifpui"
    ]

    try:
        # Parse line items
        line_items = proposal_content.get("blocks", [])
        if not line_items:
            line_items = proposal_content.get("line_items", [])

        for item in line_items:
            item_name = item.get("name", "")
            item_description = item.get("description", "")

            # Detect "Merk" blocks
            merk_match = re.search(r"Merk\s+(\d+):?\s*(.*)", item_name, re.IGNORECASE)
            if merk_match:
                current_brand = f"Merk {merk_match.group(1)}"
                continue

            # Detect coupled variants (D1. D2. D3.)
            variants_match = re.findall(r"D(\d+)\.", item_name)
            is_coupled = len(variants_match) > 1

            if is_coupled:
                # Create separate elements for each variant
                element_group_id = f"{proposal_nr}_group_{element_index}"
                for variant_num in variants_match:
                    element = _parse_single_element(
                        item=item,
                        brand=current_brand,
                        variant=f"D{variant_num}",
                        coupled=True,
                        element_group_id=element_group_id,
                        proposal_nr=proposal_nr,
                        element_index=element_index
                    )
                    elements.append(element)
                    element_index += 1
            else:
                # Single element
                element = _parse_single_element(
                    item=item,
                    brand=current_brand,
                    variant=None,
                    coupled=False,
                    element_group_id=None,
                    proposal_nr=proposal_nr,
                    element_index=element_index
                )
                elements.append(element)
                element_index += 1

        logger.info(f"Parsed {len(elements)} construction elements from {proposal_nr}")
        return elements

    except Exception as e:
        logger.error(f"Failed to parse elements: {e}")
        return []


def _parse_single_element(
    item: dict,
    brand: Optional[str],
    variant: Optional[str],
    coupled: bool,
    element_group_id: Optional[str],
    proposal_nr: str,
    element_index: int
) -> Dict[str, Any]:
    """Helper to parse a single element from a line item."""

    item_name = item.get("name", "")
    item_description = item.get("description", "")

    # Extract dimensions (e.g., "1200x2400mm" or "1200 x 2400 mm")
    dimensions_match = re.search(r"(\d+)\s*x\s*(\d+)\s*mm", item_description, re.IGNORECASE)
    width_mm = int(dimensions_match.group(1)) if dimensions_match else None
    height_mm = int(dimensions_match.group(2)) if dimensions_match else None

    # Extract element type
    element_type = "Overig"
    ELEMENT_TYPES = ["Draaikiep raam", "Vast raam", "Voordeur", "Achterdeur", "Tuindeur", "Schuifpui"]
    for etype in ELEMENT_TYPES:
        if etype.lower() in item_name.lower():
            element_type = etype
            break

    return {
        "element_id": f"{proposal_nr}_{element_index}",
        "type": element_type,
        "brand": brand or "Onbekend",
        "location": None,  # TODO: Extract from description if present
        "width_mm": width_mm,
        "height_mm": height_mm,
        "coupled": coupled,
        "variant": variant,
        "price": float(item.get("price", 0.0)),
        "notes": item_description
    }


# ============================================================================
# Tool 4: transform_proposal_to_table_records
# ============================================================================

def transform_proposal_to_table_records(
    proposal: dict,
    elements: List[dict]
) -> Dict[str, List[Dict]]:
    """
    Transform Offorte data to Airtable table schemas.

    Args:
        proposal: Complete proposal data
        elements: Parsed construction elements

    Returns:
        Dictionary mapping table_name to list of records
    """
    try:
        records = {}

        # Customer Portal (klantenportaal)
        records["klantenportaal"] = _transform_customer_portal(proposal)

        # Projects (projecten)
        records["projecten"] = _transform_projects(proposal)

        # Elements Review (elementen_review)
        records["elementen_review"] = _transform_elements(proposal, elements)

        # Measurement Planning (inmeetplanning)
        records["inmeetplanning"] = _transform_measurement_planning(proposal, elements)

        # Invoicing (facturatie) - 3 splits
        records["facturatie"] = _transform_invoices(proposal)

        # Door Specifications (deur_specificaties)
        records["deur_specificaties"] = _transform_door_specs(proposal, elements)

        logger.info(f"Transformed data for {len(records)} tables")
        return records

    except Exception as e:
        logger.error(f"Failed to transform proposal data: {e}")
        return {}


def _transform_customer_portal(proposal: dict) -> List[dict]:
    """Transform to klantenportaal table format."""
    company = proposal.get("company", {})
    contacts = proposal.get("contacts", [])

    return [{
        "Bedrijfsnaam": company.get("name", ""),
        "Adres": company.get("street", ""),
        "Postcode": company.get("zipcode", ""),
        "Plaats": company.get("city", ""),
        "Email": company.get("email", ""),
        "Telefoon": company.get("phone", ""),
        "Contact Persoon": contacts[0].get("name", "") if contacts else "",
        "Offerte Nummer": proposal.get("proposal_nr", ""),
        "Status": "Actief"
    }]


def _transform_projects(proposal: dict) -> List[dict]:
    """Transform to projecten table format."""
    company = proposal.get("company", {})
    project_date = _today()
    end_date = _add_days(project_date, 60)

    return [{
        "Project Nummer": proposal.get("proposal_nr", ""),
        "Naam": proposal.get("name", ""),
        "Klant": company.get("name", ""),
        "Totaal Bedrag": float(proposal.get("total_price", 0.0)),
        "Start Datum": project_date,
        "Eind Datum": end_date,
        "Status": "Gewonnen",
        "Verantwoordelijke": proposal.get("account_user_name", ""),
        "Offorte ID": str(proposal.get("id", ""))
    }]


def _transform_elements(proposal: dict, elements: List[dict]) -> List[dict]:
    """Transform to elementen_review table format."""
    proposal_nr = proposal.get("proposal_nr", "")

    return [
        {
            "Order Nummer": proposal_nr,
            "Element ID": elem["element_id"],
            "Type": elem["type"],
            "Merk": elem["brand"],
            "Locatie": elem.get("location") or "",
            "Breedte (mm)": elem.get("width_mm"),
            "Hoogte (mm)": elem.get("height_mm"),
            "Gekoppeld": elem["coupled"],
            "Variant": elem.get("variant") or "",
            "Prijs": elem["price"],
            "Opmerkingen": elem.get("notes") or ""
        }
        for elem in elements
    ]


def _transform_measurement_planning(proposal: dict, elements: List[dict]) -> List[dict]:
    """Transform to inmeetplanning table format."""
    company = proposal.get("company", {})

    return [{
        "Order Nummer": proposal.get("proposal_nr", ""),
        "Klant": company.get("name", ""),
        "Aantal Elementen": len(elements),
        "Geschatte Tijd (min)": len(elements) * 18,  # 18 min per element
        "Geplande Datum": "",  # Manual assignment
        "Status": "Te plannen",
        "Toegewezen aan": None
    }]


def _transform_invoices(proposal: dict) -> List[dict]:
    """Transform to facturatie table format with 30/65/5 splits."""
    total = float(proposal.get("total_price", 0.0))
    proposal_nr = proposal.get("proposal_nr", "")
    today = _today()
    project_start = _add_days(today, 14)
    project_end = _add_days(today, 74)

    return [
        {
            "Order Nummer": proposal_nr,
            "Factuur Type": "30% - Vooraf",
            "Bedrag": round(total * 0.30, 2),
            "Datum": today,
            "Status": "Concept"
        },
        {
            "Order Nummer": proposal_nr,
            "Factuur Type": "65% - Start",
            "Bedrag": round(total * 0.65, 2),
            "Datum": project_start,
            "Status": "Gepland"
        },
        {
            "Order Nummer": proposal_nr,
            "Factuur Type": "5% - Oplevering",
            "Bedrag": round(total * 0.05, 2),
            "Datum": project_end,
            "Status": "Gepland"
        }
    ]


def _transform_door_specs(proposal: dict, elements: List[dict]) -> List[dict]:
    """Transform to deur_specificaties table format (only door elements)."""
    door_elements = [e for e in elements if "deur" in e["type"].lower()]

    return [
        {
            "Order Nummer": proposal.get("proposal_nr", ""),
            "Deur Type": elem["type"],
            "Model": "",  # TODO: Extract from notes
            "Kleur": "",  # TODO: Extract from notes
            "Glastype": "",  # TODO: Extract from notes
            "Sluitwerk": "",  # TODO: Extract from notes
            "Speciale Kenmerken": elem.get("notes") or ""
        }
        for elem in door_elements
    ]


# Helper functions
def _today() -> str:
    """Current date in DD-MM-YYYY format."""
    return datetime.now().strftime("%d-%m-%Y")


def _add_days(date_str: str, days: int) -> str:
    """Add days to DD-MM-YYYY format date."""
    try:
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
        new_date = date_obj + timedelta(days=days)
        return new_date.strftime("%d-%m-%Y")
    except:
        # Fallback if parsing fails
        new_date = datetime.now() + timedelta(days=days)
        return new_date.strftime("%d-%m-%Y")


# ============================================================================
# Tool 5: sync_to_airtable
# ============================================================================

async def sync_to_airtable(
    ctx: RunContext[AgentDependencies],
    base_id: str,
    table_name: str,
    records: List[dict],
    key_field: str = "Order Nummer"
) -> Dict[str, Any]:
    """
    Create/update records in Airtable with batch operations.

    Args:
        ctx: Agent run context
        base_id: Airtable base ID
        table_name: Table name within base
        records: Records to sync
        key_field: Field to check for duplicates

    Returns:
        Dict with sync statistics
    """
    deps = ctx.deps

    try:
        api = AirtableApi(deps.airtable_api_key)
        table = api.table(base_id, table_name)

        created_count = 0
        updated_count = 0
        failed_count = 0
        record_ids = []
        errors = []

        # Process in batches of 10 (Airtable limit)
        batch_size = 10
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            try:
                # Upsert logic: check if records exist
                for record in batch:
                    key_value = record.get(key_field)
                    if key_value:
                        # Search for existing record
                        formula = f"{{{key_field}}} = '{key_value}'"
                        existing = table.all(formula=formula)

                        if existing:
                            # Update existing
                            updated = table.update(existing[0]["id"], record)
                            record_ids.append(updated["id"])
                            updated_count += 1
                        else:
                            # Create new
                            created = table.create(record)
                            record_ids.append(created["id"])
                            created_count += 1
                    else:
                        # No key field, just create
                        created = table.create(record)
                        record_ids.append(created["id"])
                        created_count += 1

                # Rate limit: 5 req/sec = 0.2s between requests
                await asyncio.sleep(0.21)

            except Exception as batch_error:
                logger.error(f"Batch sync error for {table_name}: {batch_error}")
                errors.append(str(batch_error))
                failed_count += len(batch)

        logger.info(
            f"Synced to {table_name}: {created_count} created, {updated_count} updated, {failed_count} failed"
        )

        return {
            "success": failed_count == 0,
            "created": created_count,
            "updated": updated_count,
            "failed": failed_count,
            "record_ids": record_ids,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Failed to sync to Airtable table {table_name}: {e}")
        return {
            "success": False,
            "created": 0,
            "updated": 0,
            "failed": len(records),
            "record_ids": [],
            "errors": [str(e)]
        }


# ============================================================================
# Tool 6: process_won_proposal
# ============================================================================

async def process_won_proposal(
    ctx: RunContext[AgentDependencies],
    proposal_id: int
) -> Dict[str, Any]:
    """
    End-to-end orchestration of proposal sync.

    Args:
        ctx: Agent run context
        proposal_id: Offorte proposal ID

    Returns:
        Dict with complete sync status
    """
    correlation_id = str(uuid4())
    start_time = time.time()
    deps = ctx.deps

    logger.info(f"Starting sync {correlation_id} for proposal {proposal_id}")

    try:
        # Step 1: Fetch proposal data
        proposal = await fetch_proposal_data(ctx, proposal_id, include_content=True)
        if "error" in proposal:
            return {
                "success": False,
                "error": proposal["error"],
                "correlation_id": correlation_id
            }

        # Step 2: Parse construction elements
        proposal_content = proposal.get("content", {})
        elements = parse_construction_elements(proposal_content, proposal.get("proposal_nr", ""))

        # Step 3: Transform to table records
        table_records = transform_proposal_to_table_records(proposal, elements)

        # Step 4: Sync to all 6 Airtable tables
        sync_summary = {}
        errors = []

        # Base ID mapping
        base_mapping = {
            "klantenportaal": deps.airtable_base_stb_administratie,
            "projecten": deps.airtable_base_stb_administratie,
            "facturatie": deps.airtable_base_stb_administratie,
            "elementen_review": deps.airtable_base_stb_sales,
            "inmeetplanning": deps.airtable_base_stb_productie,
            "deur_specificaties": deps.airtable_base_stb_productie,
        }

        for table_name, records in table_records.items():
            if not records:  # Skip empty tables
                continue

            base_id = base_mapping.get(table_name, deps.airtable_base_stb_administratie)

            result = await sync_to_airtable(
                ctx,
                base_id,
                table_name,
                records,
                key_field="Order Nummer" if table_name != "klantenportaal" else "Offerte Nummer"
            )

            sync_summary[table_name] = {
                "created": result["created"],
                "updated": result["updated"]
            }

            if result["failed"] > 0:
                errors.extend(result["errors"])

        # Step 5: Calculate totals
        total_created = sum(s["created"] for s in sync_summary.values())
        total_updated = sum(s["updated"] for s in sync_summary.values())
        processing_time = time.time() - start_time

        report = {
            "success": len(errors) == 0,
            "proposal_id": proposal_id,
            "proposal_nr": proposal.get("proposal_nr", ""),
            "sync_summary": sync_summary,
            "total_records_created": total_created,
            "total_records_updated": total_updated,
            "processing_time_seconds": round(processing_time, 2),
            "correlation_id": correlation_id,
            "errors": errors
        }

        logger.info(f"Completed sync {correlation_id}: success={report['success']}")
        return report

    except Exception as e:
        logger.error(f"Critical failure in sync {correlation_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "correlation_id": correlation_id,
            "processing_time_seconds": round(time.time() - start_time, 2)
        }
