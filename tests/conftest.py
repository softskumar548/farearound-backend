import importlib
import os
import sys
from pathlib import Path

import pytest


# Make sure `backend/` is on sys.path so `import app.main` works
# even under pytest import modes on Windows.
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    # Ensure env is set before importing app.main (it reads settings at import time).
    db_dir = tmp_path_factory.mktemp("db")
    os.environ.pop("DATABASE_URL", None)
    os.environ["DB_PATH"] = str(db_dir / "test.db")
    os.environ.setdefault("ALLOW_ORIGINS", "http://localhost:4200")

    import app.main as main
    importlib.reload(main)

    from fastapi.testclient import TestClient

    with TestClient(main.app) as c:
        yield c
