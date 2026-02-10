"""Amadeus wrapper with token caching, retries, and a simple TTL cache for responses.

This implementation is intentionally dependency-free and uses httpx sync client.
It provides:
- client credentials token caching (honors `expires_in` when available)
- retry with exponential backoff for 5xx and network errors
- handling for 429 (Retry-After header)
- a small in-memory TTL cache to reduce duplicate requests
"""
from typing import Any, Dict, Optional
import time
import json
import logging
import threading
from collections import OrderedDict

import httpx

from ..core.config import get_settings

logger = logging.getLogger("farearound.amadeus")
settings = get_settings()

# Use configured base URL (from .env or environment). Keep defaults in Settings.
AMADEUS_TOKEN_URL = f"{settings.amadeus_base_url.rstrip('/')}/v1/security/oauth2/token"
AMADEUS_API_BASE = settings.amadeus_base_url.rstrip('/')


class TTLCache:
    """Simple thread-safe TTL cache with maxsize eviction (LRU-ish).

    Not persistent — suitable for single process caching to reduce duplicate
    API calls during short windows.
    """

    def __init__(self, ttl: int = 60, maxsize: int = 256):
        self.ttl = ttl
        self.maxsize = maxsize
        self._lock = threading.Lock()
        self._data: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()

    def _evict_if_needed(self):
        while len(self._data) > self.maxsize:
            self._data.popitem(last=False)

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            ts, value = item
            if ts + self.ttl < now:
                # expired
                del self._data[key]
                return None
            # refresh LRU
            self._data.move_to_end(key)
            return value

    def set(self, key: str, value: Any):
        with self._lock:
            self._data[key] = (time.time(), value)
            self._data.move_to_end(key)
            self._evict_if_needed()


# module-level caches
_token_lock = threading.Lock()
_token: Optional[str] = None
_token_expiry: float = 0.0

_response_cache = TTLCache(ttl=60, maxsize=512)


def _now_ts() -> float:
    return time.time()


def _get_token() -> str:
    """Get a cached access token or request a new one."""
    global _token, _token_expiry
    with _token_lock:
        if _token and _token_expiry - 10 > _now_ts():
            return _token

        data = {
            "grant_type": "client_credentials",
            "client_id": settings.amadeus_client_id,
            "client_secret": settings.amadeus_client_secret,
        }
        try:
            with httpx.Client(timeout=10) as client:
                r = client.post(AMADEUS_TOKEN_URL, data=data)
                r.raise_for_status()
                body = r.json()
                token = body.get("access_token")
                expires_in = int(body.get("expires_in", 3600))
                _token = token
                _token_expiry = _now_ts() + expires_in
                logger.debug("Obtained Amadeus token; expires_in=%s", expires_in)
                return token
        except Exception:
            logger.exception("Failed to obtain Amadeus token")
            raise


def _make_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
    try:
        key = json.dumps({"e": endpoint, "p": params}, sort_keys=True, default=str)
    except Exception:
        key = f"{endpoint}:{str(params)}"
    return key


def _request_with_retries(method: str, url: str, params: Dict[str, Any], max_attempts: int = 4) -> Dict[str, Any]:
    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        token = _get_token()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            with httpx.Client(timeout=20) as client:
                r = client.request(method, url, params=params, headers=headers)
                if r.status_code == 429:
                    # rate limited
                    retry_after = r.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after and retry_after.isdigit() else backoff
                    logger.warning("Amadeus rate limited (429); sleeping %s seconds", wait)
                    time.sleep(wait)
                    backoff *= 2
                    continue
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if 500 <= status < 600 and attempt < max_attempts:
                logger.warning("Server error %s on attempt %s; backing off %s", status, attempt, backoff)
                time.sleep(backoff)
                backoff *= 2
                continue
            logger.exception("HTTP error during Amadeus request: %s", e)
            raise
        except httpx.RequestError as e:
            if attempt < max_attempts:
                logger.warning("Network error on attempt %s: %s; retrying after %s", attempt, e, backoff)
                time.sleep(backoff)
                backoff *= 2
                continue
            logger.exception("Network error final attempt: %s", e)
            raise

    raise RuntimeError("Failed to complete request after retries")


def search_flights(params: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = f"{AMADEUS_API_BASE}/v2/shopping/flight-offers"
    key = _make_cache_key(endpoint, params)
    cached = _response_cache.get(key)
    if cached is not None:
        logger.debug("Returning cached flights for key=%s", key)
        return cached

    data = _request_with_retries("GET", endpoint, params=params)
    _response_cache.set(key, data)
    return data


def search_hotels(params: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = f"{AMADEUS_API_BASE}/v1/shopping/hotel-offers"
    key = _make_cache_key(endpoint, params)
    cached = _response_cache.get(key)
    if cached is not None:
        logger.debug("Returning cached hotels for key=%s", key)
        return cached

    data = _request_with_retries("GET", endpoint, params=params)
    _response_cache.set(key, data)
    return data
