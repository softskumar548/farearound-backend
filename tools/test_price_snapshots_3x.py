"""E2E verification: hit flight search 3 times, then confirm 3 new snapshot rows exist.

Prereqs:
- API running on http://localhost:8000
- Amadeus creds configured so /api/search/flights returns insight (otherwise inserts are skipped)

Run from repo root:
  python backend/tools/test_price_snapshots_3x.py
"""

import sys
import pathlib
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.db import count_price_snapshots, resolve_db_path


def main() -> int:
    base_url = "http://localhost:8000"
    url = f"{base_url}/api/search/flights"
    params = {
        "origin": "BLR",
        "destination": "DXB",
        "departureDate": "2026-04-30",
        "adults": 1,
        "nonStop": "false",
        "max": 10,
    }

    before = count_price_snapshots()
    print("DB:", resolve_db_path())
    print("count(before)=", before)

    with httpx.Client(timeout=60) as client:
        for i in range(3):
            r = client.get(url, params=params)
            print(f"request {i+1} status=", r.status_code)
            if r.status_code != 200:
                print("body=", r.text)
                return 2
            body = r.json()
            if not body.get("insight"):
                print("No insight computed; snapshot insert is skipped by policy.")
                print("body.insight=", body.get("insight"))
                return 3
            time.sleep(0.2)

    after = count_price_snapshots()
    print("count(after)=", after)
    delta = after - before
    if delta != 3:
        print("Expected +3 rows, got", delta)
        return 1

    print("OK: +3 snapshot rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
