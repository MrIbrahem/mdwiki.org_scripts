"""Unit tests for flask_app/main_app/app_routes/admin/admins_required.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from flask_app.main_app.app_routes.admin.admins_required import admin_required


class TestAdminRequired:
    def test_no_user_redirects_to_login(self, app):
        @admin_required
        def view():
            return "ok"

        with app.test_request_context("/admin"):
            with patch("flask_app.main_app.app_routes.admin.admins_required.current_user", return_value=None):
                response = view()
                assert response.status_code == 302
                assert "/login" in response.location

    def test_non_admin_gets_403(self, app):
        @admin_required
        def view():
            return "ok"

        with app.test_request_context("/admin"):
            user = MagicMock()
            user.username = "regular_user"
            with patch("flask_app.main_app.app_routes.admin.admins_required.current_user", return_value=user):
                with patch("flask_app.main_app.app_routes.admin.admins_required.active_coordinators", return_value=["admin"]):
                    with pytest.raises(Exception):
                        view()

    def test_admin_passes_through(self, app):
        @admin_required
        def view():
            return "ok"

        with app.test_request_context("/admin"):
            user = MagicMock()
            user.username = "admin_user"
            with patch("flask_app.main_app.app_routes.admin.admins_required.current_user", return_value=user):
                with patch("flask_app.main_app.app_routes.admin.admins_required.active_coordinators", return_value=["admin_user"]):
                    result = view()
                    assert result == "ok"

    def test_preserves_function_name(self, app):
        @admin_required
        def my_view():
            return "ok"

        assert my_view.__name__ == "my_view"
