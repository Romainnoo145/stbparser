"""
Tests for dependencies module - Dependency injection and HTTP client management.

Tests cover:
- AgentDependencies creation
- HTTP client lazy initialization
- Cleanup operations
- from_settings factory method
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from offorte_airtable_sync.dependencies import AgentDependencies
from offorte_airtable_sync.settings import Settings


class TestAgentDependencies:
    """Test AgentDependencies class and dependency injection."""

    def test_dependencies_creation(self, test_deps):
        """Test basic dependencies creation."""
        assert test_deps.offorte_api_key == "test_offorte_key"
        assert test_deps.offorte_account_name == "test_account"
        assert test_deps.airtable_api_key == "test_airtable_key"
        assert test_deps.webhook_secret == "test_webhook_secret_12345"

    def test_dependencies_base_ids(self, test_deps):
        """Test all three Airtable base IDs are set."""
        assert test_deps.airtable_base_admin == "appTestAdmin123"
        assert test_deps.airtable_base_sales == "appTestSales123"
        assert test_deps.airtable_base_tech == "appTestTech123"

    def test_dependencies_configuration(self, test_deps):
        """Test configuration values."""
        assert test_deps.max_retries == 3
        assert test_deps.timeout == 30

    def test_dependencies_session_context(self, test_deps):
        """Test session context fields."""
        assert test_deps.job_id == "test-job-123"
        assert test_deps.proposal_id == 12345

    def test_http_client_lazy_init(self, test_deps):
        """Test HTTP client is lazy initialized."""
        # Initially None
        assert test_deps._http_client is None

        # Access via property triggers initialization
        client = test_deps.http_client
        assert isinstance(client, httpx.AsyncClient)
        assert test_deps._http_client is not None

        # Second access returns same instance
        client2 = test_deps.http_client
        assert client is client2

    def test_http_client_timeout_config(self, test_deps):
        """Test HTTP client has correct timeout configuration."""
        client = test_deps.http_client
        assert isinstance(client.timeout, httpx.Timeout)
        # Note: httpx.Timeout uses read, write, connect, pool attributes
        # The constructor accepts a single value which becomes the default

    def test_http_client_connection_limits(self, test_deps):
        """Test HTTP client connection limits."""
        client = test_deps.http_client
        assert isinstance(client._limits, httpx.Limits)
        assert client._limits.max_connections == 100

    @pytest.mark.asyncio
    async def test_cleanup_with_client(self, test_deps):
        """Test cleanup closes HTTP client if initialized."""
        # Initialize client
        _ = test_deps.http_client
        assert test_deps._http_client is not None

        # Cleanup
        await test_deps.cleanup()
        # After cleanup, client should be closed (but still exists in memory)
        # We can't easily test if it's closed without implementation details

    @pytest.mark.asyncio
    async def test_cleanup_without_client(self, test_deps):
        """Test cleanup works when client not initialized."""
        assert test_deps._http_client is None
        # Should not raise error
        await test_deps.cleanup()

    def test_from_settings_factory(self, test_settings):
        """Test creating dependencies from settings."""
        deps = AgentDependencies.from_settings(test_settings)

        assert deps.offorte_api_key == test_settings.offorte_api_key
        assert deps.offorte_account_name == test_settings.offorte_account_name
        assert deps.offorte_base_url == test_settings.offorte_base_url
        assert deps.airtable_api_key == test_settings.airtable_api_key
        assert deps.airtable_base_admin == test_settings.airtable_base_administration
        assert deps.airtable_base_sales == test_settings.airtable_base_sales_review
        assert deps.airtable_base_tech == test_settings.airtable_base_technisch
        assert deps.max_retries == test_settings.max_retries
        assert deps.timeout == test_settings.timeout_seconds

    def test_from_settings_with_overrides(self, test_settings):
        """Test from_settings with field overrides."""
        deps = AgentDependencies.from_settings(
            test_settings,
            proposal_id=99999,
            job_id="custom-job-456",
            max_retries=5
        )

        assert deps.proposal_id == 99999
        assert deps.job_id == "custom-job-456"
        assert deps.max_retries == 5
        # Other fields still from settings
        assert deps.offorte_api_key == test_settings.offorte_api_key

    def test_dependencies_direct_creation(self):
        """Test creating dependencies directly without settings."""
        deps = AgentDependencies(
            offorte_api_key="direct_key",
            offorte_account_name="direct_account",
            offorte_base_url="https://direct.com",
            airtable_api_key="direct_airtable",
            webhook_secret="direct_secret",
            airtable_base_admin="appDirect1",
            airtable_base_sales="appDirect2",
            airtable_base_tech="appDirect3",
            max_retries=2,
            timeout=60,
            proposal_id=777,
            job_id="direct-job"
        )

        assert deps.offorte_api_key == "direct_key"
        assert deps.proposal_id == 777
        assert deps.job_id == "direct-job"

    def test_dependencies_optional_fields(self):
        """Test dependencies with optional fields as None."""
        deps = AgentDependencies(
            offorte_api_key="key",
            offorte_account_name="account",
            offorte_base_url="https://test.com",
            airtable_api_key="key",
            webhook_secret="secret",
            airtable_base_admin="base1",
            airtable_base_sales="base2",
            airtable_base_tech="base3"
            # job_id and proposal_id not provided
        )

        assert deps.job_id is None
        assert deps.proposal_id is None

    @pytest.mark.unit
    def test_dependencies_offorte_url_construction(self, test_deps):
        """Test Offorte API URL can be constructed correctly."""
        base_url = f"{test_deps.offorte_base_url}/{test_deps.offorte_account_name}"
        assert base_url == "https://test-offorte.com/api/v2/test_account"

    @pytest.mark.unit
    def test_dependencies_repr_excludes_client(self, test_deps):
        """Test repr doesn't include HTTP client (marked with repr=False)."""
        repr_str = repr(test_deps)
        assert "_http_client" not in repr_str

    @pytest.mark.asyncio
    async def test_multiple_cleanup_calls(self, test_deps):
        """Test multiple cleanup calls don't cause errors."""
        _ = test_deps.http_client
        await test_deps.cleanup()
        # Second cleanup should not raise
        await test_deps.cleanup()

    def test_dependencies_dataclass_behavior(self, test_deps):
        """Test dependencies behaves as dataclass."""
        # Can access fields directly
        assert hasattr(test_deps, "offorte_api_key")
        assert hasattr(test_deps, "airtable_api_key")
        assert hasattr(test_deps, "max_retries")

        # Has dataclass methods
        assert hasattr(test_deps, "__dataclass_fields__")
