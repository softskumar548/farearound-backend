from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from ..core.config import get_settings


DDL = """
CREATE TABLE IF NOT EXISTS price_snapshots (
    id BIGSERIAL PRIMARY KEY,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    route TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    best_price NUMERIC NOT NULL,
    currency TEXT NOT NULL,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS price_alert_leads (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    last_seen_price NUMERIC,
    currency TEXT,
    created_at TEXT NOT NULL
);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_price_snapshots_route_date
ON price_snapshots(route, departure_date);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_captured_at
ON price_snapshots(captured_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_price_alert_leads_email_route_date
ON price_alert_leads(email, origin, destination, departure_date);
"""


def _database_url() -> str:
    settings = get_settings()
    url = (settings.database_url or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required for PostgreSQL mode")
    return url


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    # Use autocommit=False and explicit commit to match sqlite behavior.
    conn = psycopg.connect(_database_url())
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.execute(INDEXES)
        conn.commit()


def upsert_price_alert_lead(
    *,
    email: str,
    origin: str,
    destination: str,
    departure_date: str,
    last_seen_price: object | None,
    currency: str | None,
) -> None:
    email_n = (email or "").strip().lower()
    origin_u = (origin or "").strip().upper()
    dest_u = (destination or "").strip().upper()
    currency_u = (currency or "").strip().upper() or None
    created_at = datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO price_alert_leads
                    (email, origin, destination, departure_date, last_seen_price, currency, created_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(email, origin, destination, departure_date)
                DO UPDATE SET
                    last_seen_price = EXCLUDED.last_seen_price,
                    currency = EXCLUDED.currency
                """,
                (email_n, origin_u, dest_u, departure_date, None if last_seen_price is None else str(last_seen_price), currency_u, created_at),
            )
        conn.commit()


def insert_price_snapshot(
    *,
    origin: str,
    destination: str,
    departure_date: str,
    best_price: object,
    currency: str,
    captured_at: str | None = None,
) -> None:
    origin_u = (origin or "").strip().upper()
    dest_u = (destination or "").strip().upper()
    route = f"{origin_u}-{dest_u}"
    currency_u = (currency or "").strip().upper()
    cap = captured_at or datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO price_snapshots
                  (origin, destination, route, departure_date, best_price, currency, captured_at)
                VALUES
                  (%s, %s, %s, %s, %s, %s, %s)
                """,
                (origin_u, dest_u, route, departure_date, str(best_price), currency_u, cap),
            )
        conn.commit()


def count_price_snapshots() -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM price_snapshots")
            row = cur.fetchone()
            return int(row[0] if row else 0)


def last_price_snapshots(*, limit: int = 5) -> list[tuple]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, origin, destination, route, departure_date, best_price, currency, captured_at
                FROM price_snapshots
                ORDER BY id DESC
                LIMIT %s
                """,
                (int(limit),),
            )
            return list(cur.fetchall())


def list_price_alert_leads() -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, email, origin, destination, departure_date, last_seen_price, currency, created_at
                FROM price_alert_leads
                ORDER BY id ASC
                """
            )
            rows = list(cur.fetchall())

    leads: list[dict] = []
    for r in rows:
        leads.append(
            {
                "id": int(r["id"]),
                "email": r["email"],
                "origin": r["origin"],
                "destination": r["destination"],
                "departure_date": r["departure_date"],
                "last_seen_price": float(r["last_seen_price"]) if r.get("last_seen_price") is not None else None,
                "currency": r.get("currency"),
                "created_at": r.get("created_at"),
            }
        )
    return leads


def update_price_alert_lead_last_seen(
    *,
    lead_id: int,
    last_seen_price: object | None,
    currency: str | None,
) -> None:
    currency_u = (currency or "").strip().upper() or None

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE price_alert_leads
                SET last_seen_price = %s, currency = %s
                WHERE id = %s
                """,
                (None if last_seen_price is None else str(last_seen_price), currency_u, int(lead_id)),
            )
        conn.commit()
