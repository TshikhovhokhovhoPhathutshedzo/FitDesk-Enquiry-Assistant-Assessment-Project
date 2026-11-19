"""SQLite-backed sliding-window limits shared by concurrent processes."""

import sqlite3
from math import ceil
from pathlib import Path
from time import time
from typing import Callable

from .config import BASE_DIR

RATE_LIMIT_DB = BASE_DIR / ".rate_limit.sqlite3"


class RateLimitExceeded(Exception):
    """Raised when a client or the application has used its request allowance."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Enquiry rate limit reached. Try again in "
            f"{retry_after_seconds} seconds."
        )


class RateLimiterUnavailable(RuntimeError):
    """Raised when the shared rate-limit store cannot safely check a request."""


class RateLimiter:
    """Apply per-client and shared rolling-window request limits."""

    def __init__(
        self,
        per_client_limit: int = 10,
        total_limit: int = 30,
        window_seconds: float = 60,
        database_path: str | Path = RATE_LIMIT_DB,
        clock: Callable[[], float] = time,
    ):
        if per_client_limit < 1 or total_limit < 1 or window_seconds <= 0:
            raise ValueError("Rate limits and the time window must be positive.")
        self._per_client_limit = per_client_limit
        self._total_limit = total_limit
        self._window_seconds = window_seconds
        self._database_path = Path(database_path)
        self._clock = clock

    def check(self, client_id: str) -> None:
        """Record an allowed request or raise with its earliest retry time."""
        if not isinstance(client_id, str) or not client_id.strip():
            raise ValueError("client_id must be a non-empty string.")
        client_id = client_id.strip()

        now = self._clock()
        cutoff = now - self._window_seconds

        try:
            with sqlite3.connect(self._database_path, timeout=10) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rate_limit_requests (
                        id INTEGER PRIMARY KEY,
                        client_id TEXT NOT NULL,
                        requested_at REAL NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS rate_limit_requests_by_client_time
                    ON rate_limit_requests (client_id, requested_at)
                    """
                )
                connection.execute(
                    "DELETE FROM rate_limit_requests WHERE requested_at <= ?",
                    (cutoff,),
                )
                client_count = connection.execute(
                    "SELECT COUNT(*) FROM rate_limit_requests WHERE client_id = ?",
                    (client_id,),
                ).fetchone()[0]
                total_count = connection.execute(
                    "SELECT COUNT(*) FROM rate_limit_requests"
                ).fetchone()[0]

                retry_times = []
                if client_count >= self._per_client_limit:
                    retry_times.append(
                        connection.execute(
                            """
                            SELECT requested_at FROM rate_limit_requests
                            WHERE client_id = ?
                            ORDER BY requested_at
                            LIMIT 1
                            """,
                            (client_id,),
                        ).fetchone()[0]
                        + self._window_seconds
                    )
                if total_count >= self._total_limit:
                    retry_times.append(
                        connection.execute(
                            """
                            SELECT requested_at FROM rate_limit_requests
                            ORDER BY requested_at
                            LIMIT 1
                            """
                        ).fetchone()[0]
                        + self._window_seconds
                    )

                if retry_times:
                    retry_after = max(1, ceil(max(retry_times) - now))
                    raise RateLimitExceeded(retry_after)

                connection.execute(
                    """
                    INSERT INTO rate_limit_requests (client_id, requested_at)
                    VALUES (?, ?)
                    """,
                    (client_id, now),
                )
        except RateLimitExceeded:
            raise
        except sqlite3.Error as exc:
            raise RateLimiterUnavailable(
                "Could not check the enquiry rate limit; the request was not sent."
            ) from exc


RATE_LIMITER = RateLimiter()
