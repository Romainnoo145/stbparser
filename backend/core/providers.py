"""
LLM provider configuration for the Offorte-Airtable Sync Agent.

Simple OpenAI model provider setup.
"""

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from backend.core.settings import settings


def get_llm_model() -> OpenAIModel:
    """
    Get configured OpenAI model.

    Returns:
        OpenAIModel: Configured model instance

    Raises:
        ValueError: If configuration is invalid
    """
    provider = OpenAIProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key
    )

    return OpenAIModel(settings.llm_model, provider=provider)
