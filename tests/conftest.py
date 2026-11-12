import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def isolate_status_log():
    log_path = ROOT / "status_log.json"
    if log_path.exists():
        log_path.unlink()
    yield
    if log_path.exists():
        log_path.unlink()
