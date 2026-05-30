"""Unit tests for flask_app/main_app/app_routes/admin_routes/coordinators.py."""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("app")
class TestCoordinatorRoutes:
    def test_dashboard_requires_auth(self, mock_client):
        resp = mock_client.get("/coordinators/")
        assert resp.status_code in (302, 401, 403)
