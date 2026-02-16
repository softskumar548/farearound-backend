from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.concurrency import run_in_threadpool
from datetime import date
from typing import Optional
from pydantic import BaseModel

from ..core.config import get_settings
from .amadeus_client import search_flights, search_hotels
from .flight_insight import (
    compute_flight_insight,
    extract_price_points_from_raw_offers,
    extract_price_points_from_simplified_offers,
)
from ..db.db import insert_price_snapshot, upsert_price_alert_lead
from ..services.alert_service import check_price_drops
import logging

router = APIRouter()
log = logging.getLogger("farearound.snapshots")
lead_log = logging.getLogger("farearound.leads")


class FlightInsightResponse(BaseModel):
    best_price: float
    currency: str
    recommendation: str
    reason: str
    confidence: float


class SaveLeadRequest(BaseModel):
    email: str
    origin: str
    destination: str
    departure_date: Optional[str] = None
    # Allow frontend-style camelCase too.
    departureDate: Optional[str] = None
    last_seen_price: Optional[object] = None
    currency: Optional[str] = None


@router.post("/save-lead", status_code=202)
async def save_lead(payload: SaveLeadRequest):
    departure_date_v = payload.departure_date or payload.departureDate
    if not departure_date_v:
        raise HTTPException(status_code=400, detail="departure_date is required (YYYY-MM-DD)")

    try:
        # Strict ISO date-only validation.
        date.fromisoformat(departure_date_v)
    except Exception:
        raise HTTPException(status_code=400, detail="departure_date must be YYYY-MM-DD")

    try:
        await run_in_threadpool(
            upsert_price_alert_lead,
            email=payload.email,
            origin=payload.origin,
            destination=payload.destination,
            departure_date=departure_date_v,
            last_seen_price=payload.last_seen_price,
            currency=payload.currency,
        )
    except Exception:
        lead_log.exception("Lead upsert failed (fail-open)")

    return {"status": "accepted"}


@router.post("/leads", status_code=202)
async def save_lead_public(payload: SaveLeadRequest):
    # Public alias path (keeps legacy /save-lead working)
    return await save_lead(payload)


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

        insight = None
        computed_for_snapshot = None
        try:
            points = extract_price_points_from_simplified_offers(simplified)
            computed = compute_flight_insight(points, departureDate)
            computed_for_snapshot = computed
            insight = FlightInsightResponse(
                best_price=computed.best_price,
                currency=computed.currency,
                recommendation=computed.recommendation,
                reason=computed.reason,
                confidence=computed.confidence,
            ).model_dump() if hasattr(FlightInsightResponse, 'model_dump') else FlightInsightResponse(
                best_price=computed.best_price,
                currency=computed.currency,
                recommendation=computed.recommendation,
                reason=computed.reason,
                confidence=computed.confidence,
            ).dict()
        except Exception:
            insight = None

        # Persist snapshot (fail-open). Policy: skip if insight couldn't be computed.
        if computed_for_snapshot is not None:
            try:
                await run_in_threadpool(
                    insert_price_snapshot,
                    origin=origin.upper(),
                    destination=destination.upper(),
                    departure_date=departureDate,
                    best_price=computed_for_snapshot.best_price,
                    currency=computed_for_snapshot.currency,
                )
            except Exception:
                log.exception("Snapshot insert failed (fail-open)")

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
            "insight": insight,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/insights/flight", response_model=FlightInsightResponse)
async def get_flight_insight(
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

        raw = await run_in_threadpool(search_flights, params)
        offers = raw.get("data", []) if isinstance(raw, dict) else []

        points = extract_price_points_from_raw_offers(offers)
        computed = compute_flight_insight(points, departureDate)
        return FlightInsightResponse(
            best_price=computed.best_price,
            currency=computed.currency,
            recommendation=computed.recommendation,
            reason=computed.reason,
            confidence=computed.confidence,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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


@router.post("/run-alert-check")
async def run_alert_check():
    try:
        summary = await run_in_threadpool(check_price_drops)
        return summary
    except Exception:
        lead_log.exception("run-alert-check failed")
        raise HTTPException(status_code=502, detail="Alert check failed")


@router.post("/alerts/run")
async def run_alert_check_public():
    # Public alias path (keeps legacy /run-alert-check working)
    return await run_alert_check()
