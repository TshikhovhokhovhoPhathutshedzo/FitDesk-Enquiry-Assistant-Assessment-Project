import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from fitdesk.rate_limiter import (
    RateLimitExceeded,
    RateLimiter,
    RateLimiterUnavailable,
)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_enforces_per_client_limit_and_allows_requests_after_window(tmp_path):
    clock = FakeClock()
    limiter = RateLimiter(
        per_client_limit=2,
        total_limit=6,
        database_path=tmp_path / "rate_limit.sqlite3",
        clock=clock,
    )

    limiter.check("staff-1")
    limiter.check("staff-1")
    with pytest.raises(RateLimitExceeded) as error:
        limiter.check("staff-1")

    assert error.value.retry_after_seconds == 60
    clock.now = 60
    limiter.check("staff-1")


def test_enforces_shared_limit_across_clients(tmp_path):
    limiter = RateLimiter(
        per_client_limit=2,
        total_limit=3,
        database_path=tmp_path / "rate_limit.sqlite3",
    )

    limiter.check("staff-1")
    limiter.check("staff-2")
    limiter.check("staff-3")
    with pytest.raises(RateLimitExceeded):
        limiter.check("staff-4")


def test_concurrent_requests_cannot_exceed_shared_limit(tmp_path):
    limiter = RateLimiter(
        per_client_limit=10,
        total_limit=30,
        database_path=tmp_path / "rate_limit.sqlite3",
    )

    def check(index):
        try:
            limiter.check(f"staff-{index}")
            return True
        except RateLimitExceeded:
            return False

    with ThreadPoolExecutor(max_workers=60) as pool:
        allowed = list(pool.map(check, range(60)))

    assert sum(allowed) == 30


def test_separate_processes_share_the_global_limit(tmp_path):
    database = tmp_path / "rate_limit.sqlite3"
    source = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(source), env.get("PYTHONPATH", "")])
    )
    script = """
import sys
from fitdesk.rate_limiter import RateLimiter, RateLimitExceeded
limiter = RateLimiter(per_client_limit=10, total_limit=20, database_path=sys.argv[1])
allowed = 0
for _ in range(15):
    try:
        limiter.check(sys.argv[2])
        allowed += 1
    except RateLimitExceeded:
        pass
print(allowed)
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(database), f"staff-{index}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        for index in range(3)
    ]

    counts = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=30)
        assert process.returncode == 0, f"{stdout}\n{stderr}"
        counts.append(int(stdout.strip()))

    assert sum(counts) == 20
    assert max(counts) <= 10


def test_sqlite_failure_blocks_request_with_explicit_error(tmp_path):
    limiter = RateLimiter(database_path=tmp_path / "missing" / "rate_limit.sqlite3")

    with pytest.raises(RateLimiterUnavailable, match="request was not sent"):
        limiter.check("staff-1")


def test_empty_client_id_is_rejected():
    limiter = RateLimiter()

    with pytest.raises(ValueError, match="client_id"):
        limiter.check(" ")
