import sqlite3
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class SqliteRateLimiter:
    """Persistent fixed-window request limiter for authenticated subjects."""

    def __init__(
        self,
        db_path: str = "rate_limit.db",
        max_requests: int = 10,
        window_seconds: int = 60,
    ):
        if max_requests < 1 or window_seconds < 1:
            raise ValueError("Rate-limit values must be positive")

        self.db_path = db_path
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=5)

    def _create_table(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS request_events (
                    subject TEXT NOT NULL,
                    requested_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_request_events_subject_time
                ON request_events(subject, requested_at)
                """
            )

    def check(self, subject: str, now: float = None) -> RateLimitDecision:
        current_time = time.time() if now is None else now
        window_start = current_time - self.window_seconds

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM request_events WHERE requested_at < ?",
                (window_start,),
            )
            rows = connection.execute(
                """
                SELECT requested_at
                FROM request_events
                WHERE subject = ?
                ORDER BY requested_at ASC
                """,
                (subject,),
            ).fetchall()

            if len(rows) >= self.max_requests:
                retry_after = max(
                    1,
                    int(rows[0][0] + self.window_seconds - current_time) + 1,
                )
                return RateLimitDecision(False, retry_after)

            connection.execute(
                "INSERT INTO request_events(subject, requested_at) VALUES (?, ?)",
                (subject, current_time),
            )

        return RateLimitDecision(True)
