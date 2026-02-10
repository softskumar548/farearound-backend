try:
    from pydantic import BaseSettings
except Exception:
    # pydantic v2 moved BaseSettings to pydantic-settings package
    from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    amadeus_client_id: str
    amadeus_client_secret: str
    amadeus_base_url: str = "https://test.api.amadeus.com"
    affiliate_id: str | None = None
    domain: str | None = None
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
