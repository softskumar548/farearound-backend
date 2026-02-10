from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.concurrency import run_in_threadpool
from typing import Optional

from ..core.config import get_settings
from .amadeus_client import search_flights, search_hotels

router = APIRouter()


@router.get("/search/flights")
async def get_flights(
    origin: str = Query(..., min_length=3, max_length=3, description="IATA code e.g. BLR"),
    destination: str = Query(..., min_length=3, max_length=3, description="IATA code e.g. DXB"),
    departureDate: str = Query(..., description="YYYY-MM-DD"),
    adults: int = Query(1, ge=1, le=9),
    nonStop: bool = Query(False),
    max: int = Query(20, ge=1, le=50),
):
    try:
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": departureDate,
            "adults": adults,
            "nonStop": str(nonStop).lower(),
            "max": max,
            "currencyCode": "INR",
        }

        # call sync client in threadpool to avoid blocking the event loop
        raw = await run_in_threadpool(search_flights, params)

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

        return {
            "query": {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departureDate": departureDate,
                "adults": adults,
                "nonStop": nonStop,
            },
            "count": len(simplified),
            "offers": simplified,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/search/hotels")
def get_hotels(cityCode: str = Query(...), checkIn: str = Query(...), checkOut: str = Query(...)):
    try:
        params = {"cityCode": cityCode, "checkInDate": checkIn, "checkOutDate": checkOut}
        data = search_hotels(params)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/affiliate/info")
def affiliate_info(settings=Depends(get_settings)):
    return {"affiliate_id": settings.affiliate_id, "domain": settings.domain}
