"""
Agent dependencies for dependency injection into Pydantic AI runtime.
"""

from dataclasses import dataclass, field
from typing import Optional
import httpx
from backend.core.settings import Settings


@dataclass
class AgentDependencies:
    """
    Minimal dependencies for sync agent.
    Injected into RunContext for tool access.
    """

    # API Keys (from settings)
    offorte_api_key: str
    offorte_account_name: str
    offorte_base_url: str
    airtable_api_key: str
    webhook_secret: str

    # Base IDs
    airtable_base_stb_administratie: str
    airtable_base_stb_sales: str
    airtable_base_stb_productie: str

    # Configuration
    max_retries: int = 3
    timeout: int = 30

    # Session Context
    job_id: Optional[str] = None
    proposal_id: Optional[int] = None

    # HTTP Client (lazy init)
    _http_client: Optional[httpx.AsyncClient] = field(
        default=None,
        init=False,
        repr=False
    )

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=100)
            )
        return self._http_client

    async def cleanup(self):
        """Cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()

    @classmethod
    def from_settings(cls, settings: Settings, **overrides):
        """
        Create from settings with optional overrides.

        Args:
            settings: Application settings
            **overrides: Override specific fields

        Returns:
            AgentDependencies: Configured dependencies
        """
        return cls(
            offorte_api_key=settings.offorte_api_key,
            offorte_account_name=settings.offorte_account_name,
            offorte_base_url=settings.offorte_base_url,
            airtable_api_key=settings.airtable_api_key,
            webhook_secret=settings.webhook_secret,
            airtable_base_stb_administratie=settings.airtable_base_stb_administratie,
            airtable_base_stb_sales=settings.airtable_base_stb_sales,
            airtable_base_stb_productie=settings.airtable_base_stb_productie,
            max_retries=settings.max_retries,
            timeout=settings.timeout_seconds,
            **overrides
        )
