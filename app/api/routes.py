"""
API Routes for FareAround Backend

This module defines all REST API endpoints for the FareAround travel search service.

Available endpoints:
- GET /api/search/flights - Search for flight offers
- GET /api/search/hotels - Search for hotel offers  
- GET /api/affiliate/info - Get affiliate tracking information

All endpoints use the Amadeus API client for data retrieval with automatic
caching, retry logic, and token management.
"""

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
    """
    Search for flight offers between two locations.
    
    This endpoint searches for available flights using the Amadeus Flight Offers Search API.
    Results are cached for 60 seconds to improve performance.
    
    Args:
        origin: Origin airport IATA code (3 letters, e.g., "BLR" for Bangalore)
        destination: Destination airport IATA code (3 letters, e.g., "DXB" for Dubai)
        departureDate: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers (1-9, default: 1)
        nonStop: Filter for non-stop flights only (default: False)
        max: Maximum number of results to return (1-50, default: 20)
    
    Returns:
        dict: Normalized flight search results with query parameters, count, and offers
        
    Raises:
        HTTPException: 502 if Amadeus API request fails
    """
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
    """
    Search for hotel offers in a specific city.
    
    This endpoint searches for available hotels using the Amadeus Hotel Search API.
    Results are cached for 60 seconds to improve performance.
    
    Args:
        cityCode: City IATA code (e.g., "DEL" for Delhi)
        checkIn: Check-in date in YYYY-MM-DD format
        checkOut: Check-out date in YYYY-MM-DD format
    
    Returns:
        dict: Raw Amadeus API response with hotel offers
        
    Raises:
        HTTPException: 502 if Amadeus API request fails
    """
    try:
        params = {"cityCode": cityCode, "checkInDate": checkIn, "checkOutDate": checkOut}
        data = search_hotels(params)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/affiliate/info")
def affiliate_info(settings=Depends(get_settings)):
    """
    Get configured affiliate tracking information.
    
    Returns the affiliate ID and domain configured in environment variables.
    Used for tracking affiliate referrals and monetization.
    
    Args:
        settings: Application settings (injected via FastAPI dependency)
    
    Returns:
        dict: Affiliate ID and domain (may be null if not configured)
    """
    return {"affiliate_id": settings.affiliate_id, "domain": settings.domain}
