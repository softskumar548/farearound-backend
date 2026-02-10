from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class FlightInsight:
    best_price: float
    currency: str
    recommendation: str  # "BOOK" | "WAIT"
    reason: str
    confidence: float


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def _days_to_departure(departure_date: str, today: Optional[date] = None) -> int:
    dep = _parse_iso_date(departure_date)
    now = today or date.today()
    return (dep - now).days


def _parse_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except Exception:
            return None
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        try:
            return Decimal(v)
        except InvalidOperation:
            return None
    return None


def _median(values: list[Decimal]) -> Decimal:
    values_sorted = sorted(values)
    n = len(values_sorted)
    mid = n // 2
    if n % 2 == 1:
        return values_sorted[mid]
    return (values_sorted[mid - 1] + values_sorted[mid]) / Decimal("2")


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def extract_price_points_from_raw_offers(raw_offers: Iterable[dict[str, Any]]) -> list[tuple[Decimal, str]]:
    points: list[tuple[Decimal, str]] = []
    for offer in raw_offers:
        if not isinstance(offer, dict):
            continue
        price = offer.get("price") or {}
        if not isinstance(price, dict):
            continue
        total = _parse_decimal(price.get("total"))
        currency = price.get("currency")
        if total is None or total <= 0:
            continue
        if not isinstance(currency, str) or not currency.strip():
            continue
        points.append((total, currency.strip()))
    return points


def extract_price_points_from_simplified_offers(offers: Iterable[dict[str, Any]]) -> list[tuple[Decimal, str]]:
    points: list[tuple[Decimal, str]] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        total = _parse_decimal(offer.get("total"))
        currency = offer.get("currency")
        if total is None or total <= 0:
            continue
        if not isinstance(currency, str) or not currency.strip():
            continue
        points.append((total, currency.strip()))
    return points


def compute_flight_insight(
    price_points: list[tuple[Decimal, str]],
    departure_date: str,
    today: Optional[date] = None,
) -> FlightInsight:
    if not price_points:
        raise ValueError("No valid flight prices found")

    totals = [t for (t, _c) in price_points]
    best_total = min(totals)
    median_total = _median(totals)
    best_currency = next((c for (t, c) in price_points if t == best_total), price_points[0][1])

    dtd = _days_to_departure(departure_date, today=today)
    dtd_for_rules = max(dtd, 0)

    deal = False
    spread = Decimal("0")
    if median_total > 0:
        spread = (median_total - best_total) / median_total
        deal = best_total <= (median_total * Decimal("0.88"))

    if dtd_for_rules <= 7:
        recommendation = "BOOK"
        reason = "Close to departure — prices often rise in the final week. Booking now reduces risk."
    elif deal:
        recommendation = "BOOK"
        reason = "This fare is significantly cheaper than other options right now. Lock it in."
    else:
        recommendation = "WAIT"
        reason = "Still early — prices often improve closer to departure. Set an alert and recheck in a few days."

    confidence = 0.55
    if dtd_for_rules <= 7:
        confidence += 0.20
    elif 8 <= dtd_for_rules <= 21:
        confidence += 0.10

    if deal:
        confidence += 0.10

    spread_f = float(spread) if spread is not None else 0.0
    if spread_f >= 0.18:
        confidence -= 0.08
    if spread_f <= 0.06:
        confidence += 0.05

    confidence = _clamp(confidence, 0.45, 0.85)

    return FlightInsight(
        best_price=float(best_total),
        currency=best_currency,
        recommendation=recommendation,
        reason=reason,
        confidence=confidence,
    )
