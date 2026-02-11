"""Print snapshot count + last rows from the local SQLite DB.

Run from repo root:
  python backend/tools/check_price_snapshots.py

Or from backend/:
  python tools/check_price_snapshots.py
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.db import count_price_snapshots, last_price_snapshots, resolve_db_path


def main() -> int:
    print("DB:", resolve_db_path())
    count = count_price_snapshots()
    print("count =", count)
    rows = last_price_snapshots(limit=5)
    for r in rows:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
