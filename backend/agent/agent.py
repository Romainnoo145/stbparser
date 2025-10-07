"""
Main Pydantic AI agent for Offorte-Airtable sync.

Registers all tools and provides the main entry point for proposal processing.
"""

from pydantic_ai import Agent, RunContext
from backend.core.providers import get_llm_model
from backend.core.dependencies import AgentDependencies
from backend.agent.prompts import SYSTEM_PROMPT
from backend.core.settings import settings
from backend.agent.tools import (
    fetch_proposal_data,
    parse_construction_elements,
    transform_proposal_to_table_records,
    sync_to_airtable,
    process_won_proposal
)

# Initialize agent
agent = Agent(
    get_llm_model(),
    deps_type=AgentDependencies,
    system_prompt=SYSTEM_PROMPT,
    retries=settings.max_retries
)


# Register tools with the agent
@agent.tool
async def tool_fetch_proposal(ctx: RunContext[AgentDependencies], proposal_id: int) -> dict:
    """
    Fetch complete proposal data from Offorte API.

    Args:
        ctx: Agent run context
        proposal_id: Offorte proposal ID

    Returns:
        Complete proposal data
    """
    return await fetch_proposal_data(ctx, proposal_id)


@agent.tool_plain
def tool_parse_elements(proposal_content: dict, proposal_nr: str) -> list:
    """
    Parse Dutch construction elements from proposal content.

    Args:
        proposal_content: Proposal content with line items
        proposal_nr: Proposal number for element IDs

    Returns:
        List of parsed elements
    """
    return parse_construction_elements(proposal_content, proposal_nr)


@agent.tool_plain
def tool_transform_data(proposal: dict, elements: list) -> dict:
    """
    Transform proposal data to Airtable table schemas.

    Args:
        proposal: Complete proposal data
        elements: Parsed construction elements

    Returns:
        Dictionary mapping table names to records
    """
    return transform_proposal_to_table_records(proposal, elements)


@agent.tool
async def tool_sync_airtable(
    ctx: RunContext[AgentDependencies],
    base_id: str,
    table_name: str,
    records: list,
    key_field: str = "Order Nummer"
) -> dict:
    """
    Sync records to Airtable table.

    Args:
        ctx: Agent run context
        base_id: Airtable base ID
        table_name: Table name
        records: Records to sync
        key_field: Field for upsert logic

    Returns:
        Sync result statistics
    """
    return await sync_to_airtable(ctx, base_id, table_name, records, key_field)


@agent.tool
async def tool_process_proposal(ctx: RunContext[AgentDependencies], proposal_id: int) -> dict:
    """
    Complete end-to-end processing of won proposal.

    Args:
        ctx: Agent run context
        proposal_id: Offorte proposal ID

    Returns:
        Complete sync report
    """
    return await process_won_proposal(ctx, proposal_id)


# Main entry point
async def process_proposal_sync(proposal_id: int, job_id: str) -> dict:
    """
    Main entry point for proposal sync.

    Args:
        proposal_id: Offorte proposal ID
        job_id: Background job identifier

    Returns:
        Sync status report
    """
    deps = AgentDependencies.from_settings(
        settings,
        proposal_id=proposal_id,
        job_id=job_id
    )

    try:
        result = await agent.run(
            f"Process and sync proposal {proposal_id} from Offorte to Airtable",
            deps=deps
        )
        return result.data
    finally:
        await deps.cleanup()
