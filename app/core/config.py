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
    # Database
    # If DATABASE_URL is set (e.g. postgres://...), the app will use PostgreSQL.
    # Otherwise it will fall back to SQLite using DB_PATH.
    database_url: str | None = None
    # SQLite DB file path. Relative paths resolve from backend directory.
    db_path: str = "farearound.db"

    # Email (SMTP)
    # Use Gmail SMTP for MVP: smtp.gmail.com:587 + STARTTLS.
    email_host: str | None = None
    email_port: int | None = None
    email_user: str | None = None
    email_password: str | None = None
    email_from_name: str = "FareAround Alerts"

    # CORS
    # Comma-separated list of allowed browser origins.
    # Examples:
    #   http://localhost:4200
    #   https://farearound.com,https://www.farearound.com
    allow_origins: str = "http://localhost:4200"

    def cors_allow_origins(self) -> list[str]:
        raw = (self.allow_origins or "").strip()
        if not raw:
            return []

        items: list[str] = []
        for part in raw.split(","):
            v = (part or "").strip()
            if not v:
                continue
            # Normalize: strip trailing slashes so it matches browser Origin exactly.
            while v.endswith("/"):
                v = v[:-1]
            if v and v not in items:
                items.append(v)
        return items

    class Config:
        # Resolve to backend/.env so tools can be run from repo root
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
