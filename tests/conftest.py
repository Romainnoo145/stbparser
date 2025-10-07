"""
Pytest configuration and shared fixtures for Offorte-Airtable Sync Agent tests.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel, AgentInfo
from pydantic_ai.messages import ModelMessage, ModelTextResponse

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.settings import Settings
from backend.core.dependencies import AgentDependencies
from backend.agent.agent import agent


# ============================================================================
# Test Settings Fixtures
# ============================================================================

@pytest.fixture
def test_settings():
    """Create test settings with mock values."""
    return Settings(
        # Offorte Configuration
        offorte_api_key="test_offorte_key",
        offorte_account_name="test_account",
        offorte_base_url="https://test-offorte.com/api/v2",
        offorte_rate_limit=30,

        # Airtable Configuration
        airtable_api_key="test_airtable_key",
        airtable_base_administration="appTestAdmin123",
        airtable_base_sales_review="appTestSales123",
        airtable_base_technisch="appTestTech123",
        airtable_rate_limit=5,

        # LLM Configuration
        llm_provider="openai",
        llm_api_key="test_llm_key",
        llm_model="gpt-4o",
        llm_base_url="https://api.openai.com/v1",

        # Server Configuration
        webhook_secret="test_webhook_secret_12345",
        server_port=8000,
        server_host="0.0.0.0",

        # Redis Configuration
        redis_url="redis://localhost:6379/0",

        # Application Settings
        app_env="testing",
        log_level="DEBUG",
        debug=True,
        max_retries=3,
        timeout_seconds=30
    )


@pytest.fixture
def test_deps(test_settings):
    """Create test dependencies from settings."""
    return AgentDependencies.from_settings(
        test_settings,
        proposal_id=12345,
        job_id="test-job-123"
    )


# ============================================================================
# Model Fixtures for Agent Testing
# ============================================================================

@pytest.fixture
def test_model():
    """Create TestModel for basic agent testing."""
    return TestModel()


@pytest.fixture
def test_agent_with_test_model(test_model):
    """Create agent with TestModel override for fast testing."""
    return agent.override(model=test_model)


@pytest.fixture
def function_model_simple():
    """Create FunctionModel that returns simple text responses."""
    async def simple_response(messages: list[ModelMessage], info: AgentInfo) -> ModelTextResponse:
        return ModelTextResponse(content="Processing complete")

    return FunctionModel(simple_response)


@pytest.fixture
def function_model_with_tools():
    """Create FunctionModel that simulates tool calling behavior."""
    call_count = {"count": 0}

    async def tool_calling_response(messages: list[ModelMessage], info: AgentInfo) -> ModelTextResponse | dict:
        call_count["count"] += 1

        if call_count["count"] == 1:
            # First call - analyze request
            return ModelTextResponse(content="I'll fetch the proposal data and sync to Airtable")
        elif call_count["count"] == 2:
            # Second call - call the process tool
            return {
                "tool_process_proposal": {
                    "proposal_id": 12345
                }
            }
        else:
            # Final response
            return ModelTextResponse(
                content="Successfully synced proposal 12345 to all 6 Airtable tables"
            )

    return FunctionModel(tool_calling_response)


# ============================================================================
# Mock API Response Fixtures
# ============================================================================

@pytest.fixture
def mock_offorte_proposal():
    """Mock Offorte API proposal response."""
    return {
        "id": 12345,
        "proposal_nr": "2025001NL",
        "name": "Renovatie project - Van der Berg",
        "status": "won",
        "total_price": 45000.00,
        "company_id": 678,
        "contact_ids": [234, 235],
        "account_user_name": "Jan Jansen",
        "date_created": "2025-01-15 14:30:00"
    }


@pytest.fixture
def mock_offorte_company():
    """Mock Offorte API company response."""
    return {
        "id": 678,
        "name": "Van der Berg Bouw B.V.",
        "street": "Dorpsstraat 123",
        "zipcode": "1234 AB",
        "city": "Amsterdam",
        "email": "info@vanderberg.nl",
        "phone": "+31 20 1234567"
    }


@pytest.fixture
def mock_offorte_contact():
    """Mock Offorte API contact response."""
    return {
        "id": 234,
        "name": "Pieter van der Berg",
        "email": "pieter@vanderberg.nl",
        "phone": "+31 6 12345678"
    }


@pytest.fixture
def mock_offorte_content():
    """Mock Offorte API proposal content with Dutch construction elements."""
    return {
        "blocks": [
            {
                "name": "Merk 1: Voordeur pakket",
                "description": "Complete voordeur installatie",
                "price": 0.0
            },
            {
                "name": "D1. D2. Voordeur variant",
                "description": "Draaikiep raam 1200x2400mm met dubbel glas",
                "price": 3500.00
            },
            {
                "name": "Merk 2: Ramen pakket",
                "description": "Ramen installatie woonkamer",
                "price": 0.0
            },
            {
                "name": "Vast raam woonkamer",
                "description": "Vast raam 2000x1500mm, triple glas",
                "price": 2800.00
            },
            {
                "name": "Draaikiep raam slaapkamer",
                "description": "Draaikiep raam 800x1200mm",
                "price": 1200.00
            }
        ]
    }


@pytest.fixture
def mock_webhook_payload():
    """Mock Offorte webhook payload."""
    return {
        "type": "proposal_won",
        "date_created": "2025-01-15 14:30:00",
        "data": {
            "id": 12345,
            "name": "Offerte 2025001NL",
            "status": "won",
            "total_price": 45000.00,
            "company_id": 678,
            "contact_ids": [234, 235]
        }
    }


@pytest.fixture
def mock_airtable_record():
    """Mock Airtable record response."""
    return {
        "id": "recABC123",
        "fields": {
            "Order Nummer": "2025001NL",
            "Bedrijfsnaam": "Van der Berg Bouw B.V.",
            "Status": "Actief"
        },
        "createdTime": "2025-01-15T14:30:00.000Z"
    }


# ============================================================================
# HTTP Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API calls."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.patch = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    client = AsyncMock()
    client.rpush = AsyncMock(return_value=1)
    client.lpop = AsyncMock()
    client.llen = AsyncMock(return_value=0)
    client.close = AsyncMock()
    return client


# ============================================================================
# Dutch Language Test Data
# ============================================================================

@pytest.fixture
def dutch_special_chars():
    """Dutch special characters for testing."""
    return {
        "company_name": "Bouwbedrijf Müller & Söhne B.V.",
        "contact_name": "Jerôme van der Bëek",
        "city": "'s-Hertogenbosch",
        "description": "Kunststof kozijn met triple isolatieglas",
        "price_formatted": "€ 1.234,56",
        "price_value": 1234.56
    }


@pytest.fixture
def dutch_invoice_splits():
    """Expected Dutch invoice splits."""
    return {
        "total": 45000.00,
        "vooraf": {"percentage": 0.30, "amount": 13500.00, "label": "30% - Vooraf"},
        "bij_start": {"percentage": 0.65, "amount": 29250.00, "label": "65% - Start"},
        "oplevering": {"percentage": 0.05, "amount": 2250.00, "label": "5% - Oplevering"}
    }


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with external services"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )
    config.addinivalue_line(
        "markers", "dutch: Tests for Dutch language handling"
    )
