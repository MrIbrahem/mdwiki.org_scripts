"""Unit tests for flask_app/main_app/app_routes/utils/routes_utils.py module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask_app.main_app.app_routes.utils.routes_utils import load_auth_payload


class TestLoadAuthPayload:
    def test_with_user(self):
        user = MagicMock()
        user.user_id = 42
        user.username = "TestUser"
        user.access_token = "token123"
        user.access_secret = "secret456"
        result = load_auth_payload(user)
        assert result["id"] == 42
        assert result["username"] == "TestUser"
        assert result["access_token"] == "token123"
        assert result["access_secret"] == "secret456"

    def test_with_none(self):
        result = load_auth_payload(None)
        assert result == {}

    def test_returns_dict(self):
        result = load_auth_payload(None)
        assert isinstance(result, dict)

    def test_with_user_returns_dict(self):
        user = MagicMock()
        user.user_id = 1
        user.username = "u"
        user.access_token = "t"
        user.access_secret = "s"
        result = load_auth_payload(user)
        assert isinstance(result, dict)
        assert len(result) == 4
