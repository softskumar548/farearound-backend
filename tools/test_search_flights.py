"""
End-to-end flight search test using the existing Amadeus client and normalization logic.
Run from repo root with: python backend/tools/test_search_flights.py
"""
import sys
import pathlib
import json
import asyncio

# ensure backend project root is importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.api.amadeus_client import search_flights
from app.api.flight_insight import (
    compute_flight_insight,
    extract_price_points_from_raw_offers,
)
from app.core.config import get_settings


def normalize_offers(raw: dict):
    offers = raw.get("data", []) if isinstance(raw, dict) else []
    simplified = []
    for o in offers:
        price = o.get("price", {})
        itineraries = o.get("itineraries", [])
        first_it = itineraries[0] if itineraries else {}
        segments = first_it.get("segments", [])
        duration = first_it.get("duration")
        simplified.append({
            "id": o.get("id"),
            "total": price.get("total"),
            "currency": price.get("currency"),
            "duration": duration,
            "segments": [
                {
                    "from": s.get("departure", {}).get("iataCode"),
                    "to": s.get("arrival", {}).get("iataCode"),
                    "departAt": s.get("departure", {}).get("at"),
                    "arriveAt": s.get("arrival", {}).get("at"),
                    "carrier": s.get("carrierCode"),
                    "flightNumber": s.get("number"),
                    "segmentDuration": s.get("duration"),
                }
                for s in segments
            ],
        })
    return simplified


def run_test():
    settings = get_settings()
    if not settings.amadeus_client_id or not settings.amadeus_client_secret:
        print("Missing AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET. Create backend/.env (or set env vars) and retry.")
        return 1

    params = {
        "originLocationCode": "BLR",
        "destinationLocationCode": "DXB",
        "departureDate": "2026-04-30",
        "adults": 1,
        "nonStop": "false",
        "max": 10,
        "currencyCode": "INR",
    }
    print("Requesting flight offers with params:")
    print(json.dumps(params, indent=2))
    try:
        raw = search_flights(params)
    except Exception as e:
        print("Search failed:", repr(e))
        return 2

    insight = None
    try:
        offers = raw.get("data", []) if isinstance(raw, dict) else []
        points = extract_price_points_from_raw_offers(offers)
        computed = compute_flight_insight(points, params["departureDate"])
        insight = {
            "best_price": computed.best_price,
            "currency": computed.currency,
            "recommendation": computed.recommendation,
            "reason": computed.reason,
            "confidence": computed.confidence,
        }
    except Exception as e:
        insight = {"error": str(e)}

    simplified = normalize_offers(raw)
    out = {
        "query": {
            "origin": params["originLocationCode"],
            "destination": params["destinationLocationCode"],
            "departureDate": params["departureDate"],
            "adults": params["adults"],
            "nonStop": params["nonStop"],
        },
        "count": len(simplified),
        "offers": simplified,
        "insight": insight,
    }
    print("Normalized response:")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())
