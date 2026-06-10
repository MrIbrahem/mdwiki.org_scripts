"""Unit tests for src/main_app/app_routes/auth/utils.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask import g, session

from src.main_app.app_routes.auth.utils import load_logged_in_user, load_user, oauth_required
from src.main_app.su_services.current_user import CurrentUser


class TestOauthRequired:
    def test_oauth_required_decorator_no_user(self, app):
        @oauth_required
        def protected():
            return "allowed"

        with app.test_request_context("/protected"):
            with patch("src.main_app.app_routes.auth.utils.load_user", return_value=None):
                response = protected()
                assert response.status_code == 302
                assert "/login" in response.location

    def test_oauth_required_decorator_with_user(self, app):
        @oauth_required
        def protected():
            return "allowed"

        with app.test_request_context("/protected"):
            with patch("src.main_app.app_routes.auth.utils.load_user", return_value=MagicMock()):
                response = protected()
                assert response == "allowed"


class TestLoadLoggedInUser:
    def test_current_user_from_session(self, app):
        with app.test_request_context():
            session["uid"] = 123
            fake_user = CurrentUser(user_id=123, username="test_user", access_token=b"t", access_secret=b"s")
            with patch(
                "src.main_app.su_services.users_service.UserService.get_authenticated_user",
                return_value=fake_user,
            ):
                load_logged_in_user()
                user = load_user()
                assert user == fake_user
                assert session["username"] == "test_user"
                assert g._current_user == fake_user

    def test_current_user_cached_in_g(self, app):
        with app.test_request_context():
            g._current_user = "cached_user"
            assert load_user() == "cached_user"

    def test_current_user_no_session(self, app):
        with app.test_request_context():
            # No uid in session, no cookie
            with patch("src.main_app.su_services.users_service.UserService.get_authenticated_user") as mock_get:
                user = load_user()
                assert user is None
                mock_get.assert_not_called()
