"""
Simple diagnostic script to request an Amadeus token and print the response.
Run from the repo root with: python backend/tools/test_amadeus_token.py

This reads `backend/.env` via the Settings class in `backend/app/core/config.py`.
"""
import sys
import pathlib
import httpx

# Ensure the repository `backend` folder (project root for imports) is on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings

settings = get_settings()

if not settings.amadeus_client_id or not settings.amadeus_client_secret:
    print("Missing AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET. Create backend/.env (or set env vars) and retry.")
    sys.exit(1)

base = settings.amadeus_base_url.rstrip("/")
url = f"{base}/v1/security/oauth2/token"

data = {
    "grant_type": "client_credentials",
    "client_id": settings.amadeus_client_id,
    "client_secret": settings.amadeus_client_secret,
}

print("Requesting token from:", url)
try:
    with httpx.Client(timeout=15) as client:
        r = client.post(url, data=data)
        print("Status:", r.status_code)
        # print headers useful for debugging (but avoid printing auth headers)
        print("Response headers:")
        for k, v in r.headers.items():
            print(f"  {k}: {v}")
        print("Body:")
        try:
            print(r.json())
        except Exception:
            print(r.text)
except Exception as e:
    print("Error making request:", e)
    sys.exit(2)

if r.status_code != 200:
    sys.exit(1)

print("Token acquired OK")
