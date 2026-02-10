"""
Configuration management for FareAround backend.

This module handles all application configuration using environment variables
via Pydantic BaseSettings. It supports both Pydantic v1 and v2 for compatibility.

Environment variables are loaded from a .env file in the project root.
"""

try:
    from pydantic import BaseSettings
except Exception:
    # pydantic v2 moved BaseSettings to pydantic-settings package
    from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be configured via a .env file or environment variables.
    Required fields will raise an error if not provided.
    
    Attributes:
        amadeus_client_id: Amadeus API client ID (required)
        amadeus_client_secret: Amadeus API client secret (required)
        amadeus_base_url: Amadeus API base URL (default: test environment)
        affiliate_id: Optional affiliate tracking ID
        domain: Optional domain name for affiliate tracking
        port: Server port number (default: 8000)
    """
    
    amadeus_client_id: str
    amadeus_client_secret: str
    amadeus_base_url: str = "https://test.api.amadeus.com"
    affiliate_id: str | None = None
    domain: str | None = None
    port: int = 8000

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings: Configured settings object with all environment variables loaded.
        
    Raises:
        ValidationError: If required environment variables are missing.
    """
    return Settings()
