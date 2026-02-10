from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from ..core.config import get_settings


DDL = """
CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    route TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    best_price NUMERIC NOT NULL,
    currency TEXT NOT NULL,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS price_alert_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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


def resolve_db_path() -> str:
    """Resolve the SQLite DB path.

    - If DB_PATH is absolute, use it.
    - If relative, resolve against the backend directory (backend/).
    - Ensure parent directory exists if a directory is specified.
    """
    settings = get_settings()
    raw = (settings.db_path or "farearound.db").strip()
    if not raw:
        raw = "farearound.db"

    p = Path(raw)
    if not p.is_absolute():
        backend_dir = Path(__file__).resolve().parents[2]
        p = backend_dir / p

    if p.parent and str(p.parent) not in ("", "."):
        p.parent.mkdir(parents=True, exist_ok=True)

    return str(p)


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    db_path = resolve_db_path()
    conn = sqlite3.connect(
        db_path,
        check_same_thread=False,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    try:
        # Better concurrency characteristics for a file DB.
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=3000;")
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(DDL)
        conn.executescript(INDEXES)
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
        price_v = None if last_seen_price is None else str(last_seen_price)

        with get_conn() as conn:
                conn.execute(
                        """
                        INSERT INTO price_alert_leads
                            (email, origin, destination, departure_date, last_seen_price, currency, created_at)
                        VALUES
                            (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(email, origin, destination, departure_date)
                        DO UPDATE SET
                            last_seen_price = excluded.last_seen_price,
                            currency = excluded.currency
                        """,
                        (email_n, origin_u, dest_u, departure_date, price_v, currency_u, created_at),
                )
                conn.commit()


def insert_price_snapshot(
    *,
    origin: str,
    destination: str,
    departure_date: str,
    best_price: object,
    currency: str,
    captured_at: Optional[str] = None,
) -> None:
    origin_u = (origin or "").strip().upper()
    dest_u = (destination or "").strip().upper()
    route = f"{origin_u}-{dest_u}"
    currency_u = (currency or "").strip().upper()

    cap = captured_at or datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO price_snapshots
              (origin, destination, route, departure_date, best_price, currency, captured_at)
            VALUES
              (?, ?, ?, ?, ?, ?, ?)
            """,
            (origin_u, dest_u, route, departure_date, str(best_price), currency_u, cap),
        )
        conn.commit()


def count_price_snapshots() -> int:
    with get_conn() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM price_snapshots")
        row = cur.fetchone()
        return int(row[0] if row else 0)


def last_price_snapshots(limit: int = 5) -> list[tuple]:
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT id, origin, destination, route, departure_date, best_price, currency, captured_at
            FROM price_snapshots
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        )
        return list(cur.fetchall())
