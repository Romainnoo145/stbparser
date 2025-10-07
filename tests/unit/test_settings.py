"""
Tests for settings module - environment configuration and validation.

Tests cover:
- Settings loading from environment
- Required field validation
- Default values
- Error handling for missing keys
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from offorte_airtable_sync.settings import Settings, load_settings


class TestSettings:
    """Test Settings class and configuration loading."""

    def test_settings_with_all_fields(self, test_settings):
        """Test settings creation with all required fields."""
        assert test_settings.offorte_api_key == "test_offorte_key"
        assert test_settings.offorte_account_name == "test_account"
        assert test_settings.airtable_api_key == "test_airtable_key"
        assert test_settings.llm_api_key == "test_llm_key"
        assert test_settings.webhook_secret == "test_webhook_secret_12345"

    def test_settings_default_values(self, test_settings):
        """Test settings default values are applied correctly."""
        assert test_settings.offorte_base_url == "https://test-offorte.com/api/v2"
        assert test_settings.offorte_rate_limit == 30
        assert test_settings.airtable_rate_limit == 5
        assert test_settings.server_port == 8000
        assert test_settings.server_host == "0.0.0.0"
        assert test_settings.max_retries == 3
        assert test_settings.timeout_seconds == 30

    def test_settings_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                offorte_api_key="test",
                offorte_account_name="test",
                airtable_api_key="test",
                # Missing llm_api_key
                webhook_secret="test"
            )

        assert "llm_api_key" in str(exc_info.value)

    def test_settings_case_insensitive(self):
        """Test that environment variables are case insensitive."""
        with patch.dict(os.environ, {
            "OFFORTE_API_KEY": "key1",
            "offorte_account_name": "account1",  # lowercase
            "AIRTABLE_API_KEY": "key2",
            "LLM_API_KEY": "key3",
            "WEBHOOK_SECRET": "secret1",
            "airtable_base_administration": "base1",
            "airtable_base_sales_review": "base2",
            "airtable_base_technisch": "base3"
        }):
            settings = Settings()
            assert settings.offorte_api_key == "key1"
            assert settings.offorte_account_name == "account1"

    def test_settings_extra_fields_ignored(self):
        """Test that extra fields are ignored per model config."""
        settings = Settings(
            offorte_api_key="test",
            offorte_account_name="test",
            airtable_api_key="test",
            llm_api_key="test",
            webhook_secret="test",
            airtable_base_administration="base1",
            airtable_base_sales_review="base2",
            airtable_base_technisch="base3",
            unknown_field="should_be_ignored"  # Extra field
        )
        assert not hasattr(settings, "unknown_field")

    def test_load_settings_success(self, monkeypatch):
        """Test load_settings function with valid environment."""
        env_vars = {
            "OFFORTE_API_KEY": "test_key",
            "OFFORTE_ACCOUNT_NAME": "test_account",
            "AIRTABLE_API_KEY": "test_airtable",
            "AIRTABLE_BASE_ADMINISTRATION": "appAdmin",
            "AIRTABLE_BASE_SALES_REVIEW": "appSales",
            "AIRTABLE_BASE_TECHNISCH": "appTech",
            "LLM_API_KEY": "test_llm",
            "WEBHOOK_SECRET": "test_secret"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("offorte_airtable_sync.settings.load_dotenv"):
            settings = load_settings()
            assert settings.offorte_api_key == "test_key"
            assert settings.airtable_api_key == "test_airtable"

    def test_load_settings_missing_offorte_key(self, monkeypatch):
        """Test load_settings with missing Offorte API key."""
        monkeypatch.delenv("OFFORTE_API_KEY", raising=False)

        with patch("offorte_airtable_sync.settings.load_dotenv"):
            with pytest.raises(ValueError) as exc_info:
                load_settings()

            assert "OFFORTE_API_KEY" in str(exc_info.value)

    def test_load_settings_missing_airtable_key(self, monkeypatch):
        """Test load_settings with missing Airtable API key."""
        env_vars = {
            "OFFORTE_API_KEY": "test",
            "OFFORTE_ACCOUNT_NAME": "test",
            "LLM_API_KEY": "test",
            "WEBHOOK_SECRET": "test",
            "AIRTABLE_BASE_ADMINISTRATION": "base1",
            "AIRTABLE_BASE_SALES_REVIEW": "base2",
            "AIRTABLE_BASE_TECHNISCH": "base3"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        monkeypatch.delenv("AIRTABLE_API_KEY", raising=False)

        with patch("offorte_airtable_sync.settings.load_dotenv"):
            with pytest.raises(ValueError) as exc_info:
                load_settings()

            assert "AIRTABLE_API_KEY" in str(exc_info.value)

    def test_load_settings_missing_llm_key(self, monkeypatch):
        """Test load_settings with missing LLM API key."""
        env_vars = {
            "OFFORTE_API_KEY": "test",
            "OFFORTE_ACCOUNT_NAME": "test",
            "AIRTABLE_API_KEY": "test",
            "AIRTABLE_BASE_ADMINISTRATION": "base1",
            "AIRTABLE_BASE_SALES_REVIEW": "base2",
            "AIRTABLE_BASE_TECHNISCH": "base3",
            "WEBHOOK_SECRET": "test"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        monkeypatch.delenv("LLM_API_KEY", raising=False)

        with patch("offorte_airtable_sync.settings.load_dotenv"):
            with pytest.raises(ValueError) as exc_info:
                load_settings()

            assert "LLM_API_KEY" in str(exc_info.value)

    def test_settings_redis_url_default(self, test_settings):
        """Test Redis URL has correct default."""
        assert test_settings.redis_url == "redis://localhost:6379/0"

    def test_settings_app_environment(self, test_settings):
        """Test application environment settings."""
        assert test_settings.app_env == "testing"
        assert test_settings.log_level == "DEBUG"
        assert test_settings.debug is True

    @pytest.mark.unit
    def test_settings_rate_limits(self, test_settings):
        """Test rate limit configurations."""
        assert test_settings.offorte_rate_limit == 30  # 30 req/min
        assert test_settings.airtable_rate_limit == 5  # 5 req/sec

    @pytest.mark.unit
    def test_settings_base_urls(self, test_settings):
        """Test API base URLs are configured correctly."""
        assert "offorte" in test_settings.offorte_base_url.lower()
        assert test_settings.llm_base_url == "https://api.openai.com/v1"

    def test_settings_airtable_bases(self, test_settings):
        """Test all three Airtable bases are configured."""
        assert test_settings.airtable_base_administration == "appTestAdmin123"
        assert test_settings.airtable_base_sales_review == "appTestSales123"
        assert test_settings.airtable_base_technisch == "appTestTech123"
