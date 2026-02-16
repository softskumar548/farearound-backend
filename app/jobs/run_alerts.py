from __future__ import annotations

import json
import logging
import sys

from ..db.db import init_db
from ..services.alert_service import check_price_drops


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("farearound.alert_job")

    try:
        init_db()
        summary = check_price_drops()
        # Print JSON so systemd logs are easy to parse.
        print(json.dumps(summary, sort_keys=True))
        return 0
    except Exception:
        log.exception("Alert job failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
