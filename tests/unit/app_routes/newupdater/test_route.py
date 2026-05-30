"""Unit tests for flask_app/main_app/app_routes/newupdater/route.py."""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("app")
class TestNewupdaterRoute:
    def test_requires_auth(self, mock_client):
        resp = mock_client.get("/newupdater/")
        assert resp.status_code == 302

    def test_get_with_login(self, mock_client, login, monkeypatch):
        login("TestUser")
        import flask_app.main_app.su_services.users_service as users_mod
        from flask_app.main_app.su_services.users_service import CurrentUser

        monkeypatch.setattr(
            users_mod,
            "current_user",
            lambda: CurrentUser(user_id="1", username="TestUser"),
        )
        resp = mock_client.get("/newupdater/")
        assert resp.status_code == 200
