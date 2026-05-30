"""Unit tests for flask_app/main_app/app_routes/auth/rate_limit.py."""

from __future__ import annotations

from datetime import timedelta

from flask_app.main_app.app_routes.auth.rate_limit import RateLimiter


class TestRateLimiter:
    def test_allows_within_limit(self):
        rl = RateLimiter(limit=3, period=timedelta(seconds=10))
        assert rl.allow("user1") is True
        assert rl.allow("user1") is True
        assert rl.allow("user1") is True

    def test_blocks_over_limit(self):
        rl = RateLimiter(limit=2, period=timedelta(seconds=10))
        assert rl.allow("user1") is True
        assert rl.allow("user1") is True
        assert rl.allow("user1") is False

    def test_different_keys_independent(self):
        rl = RateLimiter(limit=1, period=timedelta(seconds=10))
        assert rl.allow("user1") is True
        assert rl.allow("user1") is False
        assert rl.allow("user2") is True

    def test_try_after_when_under_limit(self):
        rl = RateLimiter(limit=5, period=timedelta(seconds=10))
        rl.allow("user1")
        result = rl.try_after("user1")
        assert result == timedelta(0)

    def test_try_after_when_over_limit(self):
        rl = RateLimiter(limit=1, period=timedelta(seconds=10))
        rl.allow("user1")
        result = rl.try_after("user1")
        assert result > timedelta(0)

    def test_limit_of_one(self):
        rl = RateLimiter(limit=1, period=timedelta(seconds=10))
        assert rl.allow("k") is True
        assert rl.allow("k") is False
