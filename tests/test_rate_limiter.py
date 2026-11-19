from concurrent.futures import ThreadPoolExecutor

import pytest

from fitdesk.rate_limiter import RateLimitExceeded, RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_enforces_per_client_limit_and_allows_requests_after_window():
    clock = FakeClock()
    limiter = RateLimiter(per_client_limit=2, total_limit=6, clock=clock)

    limiter.check("staff-1")
    limiter.check("staff-1")
    with pytest.raises(RateLimitExceeded) as error:
        limiter.check("staff-1")

    assert error.value.retry_after_seconds == 60
    clock.now = 60
    limiter.check("staff-1")


def test_enforces_shared_limit_across_clients():
    limiter = RateLimiter(per_client_limit=2, total_limit=3)

    limiter.check("staff-1")
    limiter.check("staff-2")
    limiter.check("staff-3")
    with pytest.raises(RateLimitExceeded):
        limiter.check("staff-4")


def test_concurrent_requests_cannot_exceed_shared_limit():
    limiter = RateLimiter(per_client_limit=10, total_limit=30)

    def check(index):
        try:
            limiter.check(f"staff-{index}")
            return True
        except RateLimitExceeded:
            return False

    with ThreadPoolExecutor(max_workers=60) as pool:
        allowed = list(pool.map(check, range(60)))

    assert sum(allowed) == 30


def test_empty_client_id_is_rejected():
    limiter = RateLimiter()

    with pytest.raises(ValueError, match="client_id"):
        limiter.check(" ")
