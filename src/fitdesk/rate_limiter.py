"""Thread-safe sliding-window limits for Gemini-backed enquiries."""

from collections import deque
from math import ceil
from threading import Lock
from time import monotonic
from typing import Callable


class RateLimitExceeded(Exception):
    """Raised when a client or the application has used its request allowance."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Enquiry rate limit reached. Try again in "
            f"{retry_after_seconds} seconds."
        )


class RateLimiter:
    """Apply per-client and shared rolling-window request limits."""

    def __init__(
        self,
        per_client_limit: int = 10,
        total_limit: int = 30,
        window_seconds: float = 60,
        clock: Callable[[], float] = monotonic,
    ):
        if per_client_limit < 1 or total_limit < 1 or window_seconds <= 0:
            raise ValueError("Rate limits and the time window must be positive.")
        self._per_client_limit = per_client_limit
        self._total_limit = total_limit
        self._window_seconds = window_seconds
        self._clock = clock
        self._client_requests: dict[str, deque[float]] = {}
        self._all_requests: deque[float] = deque()
        self._lock = Lock()

    def check(self, client_id: str) -> None:
        """Record an allowed request or raise with its earliest retry time."""
        if not isinstance(client_id, str) or not client_id.strip():
            raise ValueError("client_id must be a non-empty string.")
        client_id = client_id.strip()

        now = self._clock()
        cutoff = now - self._window_seconds

        with self._lock:
            self._discard_expired(self._all_requests, cutoff)
            for known_client, requests in list(self._client_requests.items()):
                self._discard_expired(requests, cutoff)
                if not requests:
                    del self._client_requests[known_client]

            client_requests = self._client_requests.get(client_id, deque())
            retry_times = []
            if len(client_requests) >= self._per_client_limit:
                retry_times.append(client_requests[0] + self._window_seconds)
            if len(self._all_requests) >= self._total_limit:
                retry_times.append(self._all_requests[0] + self._window_seconds)

            if retry_times:
                retry_after = max(1, ceil(max(retry_times) - now))
                raise RateLimitExceeded(retry_after)

            client_requests = self._client_requests.setdefault(client_id, client_requests)
            client_requests.append(now)
            self._all_requests.append(now)

    @staticmethod
    def _discard_expired(requests: deque[float], cutoff: float) -> None:
        while requests and requests[0] <= cutoff:
            requests.popleft()


RATE_LIMITER = RateLimiter()
