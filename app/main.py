from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .core.config import get_settings
from .db.db import init_db, resolve_db_path
import logging

app = FastAPI(title="FareAround AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
def _startup():
    settings = get_settings()
    log = logging.getLogger("farearound.startup")
    log.info("Starting FareAround API on port %s", settings.port)
    # Log which Amadeus base URL is configured (do NOT log secrets)
    log.info("Amadeus base URL: %s", settings.amadeus_base_url)
    if not settings.amadeus_client_id or not settings.amadeus_client_secret:
        log.warning("Amadeus client ID/secret missing; API calls will fail until set")

    try:
        init_db()
        sqlite_path = resolve_db_path()
        if sqlite_path:
            log.info("SQLite DB initialized at %s", sqlite_path)
        else:
            log.info("DB initialized (PostgreSQL)")
    except Exception:
        # Fail-open so searches can still run even if persistence is broken.
        log.exception("DB init failed (fail-open). App will continue without persistence.")
