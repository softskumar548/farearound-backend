from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from ..api.amadeus_client import search_flights
from ..api.flight_insight import extract_price_points_from_raw_offers, compute_flight_insight
from ..db.db import list_price_alert_leads, update_price_alert_lead_last_seen
from .email_service import send_price_drop_email

logger = logging.getLogger("farearound.alerts")

FORCED_CURRENCY = "INR"


def _to_decimal(v: object) -> Decimal | None:
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return None


def check_price_drops() -> dict[str, int]:
    """Check saved leads, detect price drops, and send email alerts.

    Non-negotiables:
    - Per-lead isolation: one bad lead doesn't stop the run
    - Forced INR: comparisons are apples-to-apples
    - Email gating: update DB only if email send succeeds
    - Useful summary counts
    """

    summary: dict[str, int] = {
        "leads_checked": 0,
        "initialized": 0,
        "emails_sent": 0,
        "updated": 0,
        "no_change": 0,
        "no_offers": 0,
        "errors": 0,
    }

    leads = list_price_alert_leads()

    for lead in leads:
        summary["leads_checked"] += 1

        try:
            lead_id = int(lead["id"])
            email = str(lead.get("email") or "").strip()
            origin = str(lead.get("origin") or "").strip().upper()
            destination = str(lead.get("destination") or "").strip().upper()
            departure_date = str(lead.get("departure_date") or "").strip()

            old_price = _to_decimal(lead.get("last_seen_price"))

            params: dict[str, Any] = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": 1,
                "nonStop": "false",
                "max": 20,
                "currencyCode": FORCED_CURRENCY,
            }

            raw = search_flights(params)
            offers = raw.get("data", []) if isinstance(raw, dict) else []

            points = extract_price_points_from_raw_offers(offers)
            if not points:
                summary["no_offers"] += 1
                continue

            try:
                insight = compute_flight_insight(points, departure_date)
            except ValueError:
                summary["no_offers"] += 1
                continue

            new_price = _to_decimal(getattr(insight, "best_price", None))
            if new_price is None:
                summary["no_offers"] += 1
                continue

            # 1) Baseline init (no email)
            if old_price is None:
                update_price_alert_lead_last_seen(
                    lead_id=lead_id,
                    last_seen_price=str(new_price),
                    currency=FORCED_CURRENCY,
                )
                summary["initialized"] += 1
                summary["updated"] += 1
                continue

            # 2) Drop detection
            if new_price < old_price:
                # Email first; persist only if send succeeded.
                send_price_drop_email(
                    email,
                    origin,
                    destination,
                    departure_date,
                    old_price=str(old_price),
                    new_price=str(new_price),
                    currency=FORCED_CURRENCY,
                )

                update_price_alert_lead_last_seen(
                    lead_id=lead_id,
                    last_seen_price=str(new_price),
                    currency=FORCED_CURRENCY,
                )

                summary["emails_sent"] += 1
                summary["updated"] += 1
            else:
                summary["no_change"] += 1

        except Exception:
            summary["errors"] += 1
            logger.exception("Alert check failed for lead: %s", lead)

    return summary
