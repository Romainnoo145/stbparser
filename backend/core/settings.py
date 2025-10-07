"""
Settings module for Offorte-Airtable Sync Agent.

Uses python-dotenv and pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Offorte Configuration
    offorte_api_key: str = Field(..., description="Offorte API key")
    offorte_account_name: str = Field(..., description="Offorte account name")
    offorte_base_url: str = Field(
        default="https://connect.offorte.com/api/v2",
        description="Offorte API base URL"
    )
    offorte_rate_limit: int = Field(default=30, description="Offorte requests per minute")

    # Airtable Configuration
    airtable_api_key: str = Field(..., description="Airtable API key")
    airtable_base_stb_administratie: str = Field(..., alias="airtable_base_stb-administratie", description="STB Administratie base ID")
    airtable_base_stb_sales: str = Field(..., alias="airtable_base_stb-sales", description="STB Sales base ID")
    airtable_base_stb_productie: str = Field(..., alias="airtable_base_stb-productie", description="STB Productie base ID")
    airtable_rate_limit: int = Field(default=5, description="Airtable requests per second")

    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_api_key: str = Field(..., description="API key for the LLM provider")
    llm_model: str = Field(default="gpt-4o", description="Model name to use")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the LLM API"
    )

    # Server Configuration
    webhook_secret: str = Field(..., description="Webhook validation secret")
    server_port: int = Field(default=8000, description="Server port")
    server_host: str = Field(default="0.0.0.0", description="Server host")

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Application Settings
    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: int = Field(default=30, description="Request timeout in seconds")


def load_settings() -> Settings:
    """
    Load settings with proper error handling and environment loading.

    Returns:
        Settings: Loaded application settings

    Raises:
        ValueError: If required settings are missing or invalid
    """
    # Load environment variables from .env file
    load_dotenv()

    try:
        return Settings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "llm_api_key" in str(e).lower():
            error_msg += "\nMake sure to set LLM_API_KEY in your .env file"
        if "offorte_api_key" in str(e).lower():
            error_msg += "\nMake sure to set OFFORTE_API_KEY in your .env file"
        if "airtable_api_key" in str(e).lower():
            error_msg += "\nMake sure to set AIRTABLE_API_KEY in your .env file"
        raise ValueError(error_msg) from e


# Global settings instance
settings = load_settings()
