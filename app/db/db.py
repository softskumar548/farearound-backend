from __future__ import annotations

"""Database facade.

Callers should import DB operations from this module.

Selection rules:
- If settings.database_url is set -> PostgreSQL backend.
- Else -> SQLite backend.

This keeps the rest of the app independent from the underlying DB.
"""

from typing import Callable, TypeVar

from ..core.config import get_settings


_T = TypeVar("_T")


def _using_postgres() -> bool:
    settings = get_settings()
    return bool((settings.database_url or "").strip())


def init_db() -> None:
    if _using_postgres():
        from .postgres import init_db as _init

        return _init()

    from .sqlite import init_db as _init

    return _init()


def insert_price_snapshot(*, origin: str, destination: str, departure_date: str, best_price: object, currency: str, captured_at: str | None = None) -> None:
    if _using_postgres():
        from .postgres import insert_price_snapshot as _fn

        return _fn(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            best_price=best_price,
            currency=currency,
            captured_at=captured_at,
        )

    from .sqlite import insert_price_snapshot as _fn

    return _fn(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        best_price=best_price,
        currency=currency,
        captured_at=captured_at,
    )


def upsert_price_alert_lead(*, email: str, origin: str, destination: str, departure_date: str, last_seen_price: object | None, currency: str | None) -> None:
    if _using_postgres():
        from .postgres import upsert_price_alert_lead as _fn

        return _fn(
            email=email,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            last_seen_price=last_seen_price,
            currency=currency,
        )

    from .sqlite import upsert_price_alert_lead as _fn

    return _fn(
        email=email,
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        last_seen_price=last_seen_price,
        currency=currency,
    )


def list_price_alert_leads() -> list[dict]:
    if _using_postgres():
        from .postgres import list_price_alert_leads as _fn

        return _fn()

    from .sqlite import list_price_alert_leads as _fn

    return _fn()


def update_price_alert_lead_last_seen(*, lead_id: int, last_seen_price: object | None, currency: str | None) -> None:
    if _using_postgres():
        from .postgres import update_price_alert_lead_last_seen as _fn

        return _fn(lead_id=lead_id, last_seen_price=last_seen_price, currency=currency)

    from .sqlite import update_price_alert_lead_last_seen as _fn

    return _fn(lead_id=lead_id, last_seen_price=last_seen_price, currency=currency)


# Tooling helpers (optional)

def resolve_db_path() -> str:
    """SQLite-only helper retained for tools; returns empty when using Postgres."""

    if _using_postgres():
        return ""

    from .sqlite import resolve_db_path as _fn

    return _fn()


def count_price_snapshots() -> int:
    if _using_postgres():
        from .postgres import count_price_snapshots as _fn

        return _fn()

    from .sqlite import count_price_snapshots as _fn

    return _fn()


def last_price_snapshots(limit: int = 5) -> list[tuple]:
    if _using_postgres():
        from .postgres import last_price_snapshots as _fn

        return _fn(limit=limit)

    from .sqlite import last_price_snapshots as _fn

    return _fn(limit=limit)
