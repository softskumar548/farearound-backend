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
    }
    print("Normalized response:")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())
