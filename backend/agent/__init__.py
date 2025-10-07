"""
Pydantic AI Agent Module

Contains the main agent, tools, and prompts for syncing Offorte proposals to Airtable.
"""

from .agent import agent, process_proposal_sync
from .prompts import SYSTEM_PROMPT

__all__ = ["agent", "process_proposal_sync", "SYSTEM_PROMPT"]
