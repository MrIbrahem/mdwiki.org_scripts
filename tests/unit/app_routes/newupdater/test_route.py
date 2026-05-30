"""Unit tests for flask_app/main_app/app_routes/newupdater/route.py."""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("app")
class TestNewupdaterRoute:
    def test_requires_auth(self, mock_client):
        resp = mock_client.get("/newupdater/")
        assert resp.status_code in (302, 401, 403)

    def test_get_with_login(self, mock_client, login):
        login("TestUser")
        resp = mock_client.get("/newupdater/")
        assert resp.status_code == 200
