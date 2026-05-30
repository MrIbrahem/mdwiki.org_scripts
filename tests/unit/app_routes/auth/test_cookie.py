"""Unit tests for flask_app/main_app/app_routes/auth/cookie.py."""

from __future__ import annotations

from flask_app.main_app.app_routes.auth.cookie import (
    extract_user_id,
    sign_state_token,
    sign_user_id,
    verify_state_token,
)


class TestSignAndExtractUserId:
    def test_round_trip(self):
        token = sign_user_id(42)
        assert isinstance(token, str)
        assert extract_user_id(token) == 42

    def test_different_ids(self):
        token1 = sign_user_id(1)
        token2 = sign_user_id(2)
        assert extract_user_id(token1) == 1
        assert extract_user_id(token2) == 2

    def test_invalid_token_returns_none(self):
        assert extract_user_id("not-a-valid-token") is None

    def test_empty_token_returns_none(self):
        assert extract_user_id("") is None

    def test_tampered_token_returns_none(self):
        token = sign_user_id(42)
        assert extract_user_id(token + "tamper") is None


class TestSignAndVerifyStateToken:
    def test_round_trip(self):
        token = sign_state_token("my-nonce-123")
        assert isinstance(token, str)
        assert verify_state_token(token) == "my-nonce-123"

    def test_invalid_token_returns_none(self):
        assert verify_state_token("invalid") is None

    def test_different_nonces(self):
        t1 = sign_state_token("nonce1")
        t2 = sign_state_token("nonce2")
        assert verify_state_token(t1) == "nonce1"
        assert verify_state_token(t2) == "nonce2"
