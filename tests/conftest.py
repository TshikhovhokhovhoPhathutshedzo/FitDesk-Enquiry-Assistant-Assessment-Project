import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fitdesk.rate_limiter import RateLimiter


@pytest.fixture(autouse=True)
def isolate_status_log(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "fitdesk.status_log.LOG_FILE",
        tmp_path / "status_log.json",
    )


@pytest.fixture(autouse=True)
def isolate_rate_limiter(monkeypatch):
    monkeypatch.setattr("fitdesk.cli.RATE_LIMITER", RateLimiter())
