import tempfile
import unittest
from pathlib import Path

from rate_limiter import SqliteRateLimiter


class RateLimiterTest(unittest.TestCase):
    def test_rejects_requests_over_the_limit_and_allows_after_window(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            limiter = SqliteRateLimiter(
                str(Path(temp_dir) / "rate-limit.db"),
                max_requests=2,
                window_seconds=60,
            )

            self.assertTrue(limiter.check("user-1", now=100).allowed)
            self.assertTrue(limiter.check("user-1", now=110).allowed)

            rejected = limiter.check("user-1", now=120)
            self.assertFalse(rejected.allowed)
            self.assertGreater(rejected.retry_after_seconds, 0)

            self.assertTrue(limiter.check("user-1", now=161).allowed)

    def test_tracks_authenticated_subjects_separately(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            limiter = SqliteRateLimiter(
                str(Path(temp_dir) / "rate-limit.db"),
                max_requests=1,
                window_seconds=60,
            )

            self.assertTrue(limiter.check("user-1", now=100).allowed)
            self.assertTrue(limiter.check("user-2", now=100).allowed)


if __name__ == "__main__":
    unittest.main()
