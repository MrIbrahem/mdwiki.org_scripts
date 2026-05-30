"""Unit tests for flask_app/main_app/app_routes/auth/routes.py."""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("app")
class TestAuthRoutes:
    def test_login_redirects(self, mock_client):
        resp = mock_client.get("/login")
        assert resp.status_code == 302

    def test_logout_redirects(self, mock_client):
        resp = mock_client.get("/logout")
        assert resp.status_code == 302
