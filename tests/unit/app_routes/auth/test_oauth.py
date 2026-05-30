"""Unit tests for flask_app/main_app/app_routes/auth/oauth.py."""

from __future__ import annotations

import pytest

from flask_app.main_app.app_routes.auth.oauth import (
    IDENTITY_ERROR_MESSAGE,
    OAuthIdentityError,
)


class TestOAuthIdentityError:
    def test_is_exception(self):
        assert issubclass(OAuthIdentityError, Exception)

    def test_message(self):
        exc = OAuthIdentityError("test error")
        assert str(exc) == "test error"

    def test_original_exception(self):
        original = ValueError("original")
        exc = OAuthIdentityError("wrapper", original_exception=original)
        assert exc.original_exception is original

    def test_default_original_exception_is_none(self):
        exc = OAuthIdentityError("test")
        assert exc.original_exception is None


class TestIdentityErrorMessage:
    def test_is_non_empty_string(self):
        assert isinstance(IDENTITY_ERROR_MESSAGE, str)
        assert len(IDENTITY_ERROR_MESSAGE) > 0
