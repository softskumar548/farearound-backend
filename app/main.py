"""
FareAround Backend API - Main Application

This is the main FastAPI application entry point for the FareAround travel search backend.
It provides REST API endpoints for searching flights and hotels using the Amadeus API.

The application features:
- Flight and hotel search endpoints
- Automatic Amadeus API token management
- Response caching to reduce API calls
- CORS support for web clients
- Health check endpoint
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .core.config import get_settings
import logging

# Initialize FastAPI application
app = FastAPI(
    title="FareAround AI API",
    description="Travel search API powered by Amadeus",
    version="0.1.0"
)

# Configure CORS middleware to allow cross-origin requests
# Note: In production, restrict allow_origins to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes under /api prefix
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    """
    Health check endpoint.
    
    Returns a simple status message to verify the API is running.
    Used by load balancers and monitoring systems.
    
    Returns:
        dict: Status message indicating service health
    """
    return {"status": "ok"}


@app.on_event("startup")
def _startup():
    """
    Application startup handler.
    
    Executed when the FastAPI application starts. Performs:
    - Loads and validates configuration
    - Logs startup information
    - Warns if Amadeus credentials are missing
    """
    settings = get_settings()
    log = logging.getLogger("farearound.startup")
    log.info("Starting FareAround API on port %s", settings.port)
    # Log which Amadeus base URL is configured (do NOT log secrets)
    log.info("Amadeus base URL: %s", settings.amadeus_base_url)
    if not settings.amadeus_client_id or not settings.amadeus_client_secret:
        log.warning("Amadeus client ID/secret missing; API calls will fail until set")
