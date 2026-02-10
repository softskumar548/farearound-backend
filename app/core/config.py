try:
    from pydantic import BaseSettings
except Exception:
    # pydantic v2 moved BaseSettings to pydantic-settings package
    from pydantic_settings import BaseSettings

from pathlib import Path


_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    # Credentials are optional so the API can start without secrets.
    # Amadeus-backed endpoints will raise a clear error when missing.
    amadeus_client_id: str | None = None
    amadeus_client_secret: str | None = None
    amadeus_base_url: str = "https://test.api.amadeus.com"
    affiliate_id: str | None = None
    domain: str | None = None
    port: int = 8000
    # SQLite DB file path. Relative paths resolve from backend directory.
    db_path: str = "farearound.db"

    class Config:
        # Resolve to backend/.env so tools can be run from repo root
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
