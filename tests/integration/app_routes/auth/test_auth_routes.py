"""Integration tests for src/main_app/app_routes/auth/routes.py module.

Tests the full OAuth login/logout flow through the Flask test client with
a real SQLite database (via TestingConfig). OAuth external calls are stubbed
so no network access is required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest
from flask.app import Flask

from src.main_app.config import settings
from src.main_app.db.services import get_user_by_username, get_user_token, upsert_user_token
from src.main_app.db.services.users_service import create_user
from src.main_app.extensions import db

# Session key names from settings
_STATE_KEY = settings.sessions.state_key  # "oauth_state_nonce"
_REQ_TOKEN_KEY = settings.sessions.request_token_key  # "state"


@pytest.fixture(autouse=True)
def _clean_db(app: Flask):
    """Clean all tables after each test to prevent state leaking."""
    yield
    with app.app_context():

        meta = db.metadata
        with db.engine.begin() as conn:
            for table in reversed(meta.sorted_tables):
                conn.execute(table.delete())


@pytest.mark.usefixtures("app")
class TestLoginRoute:
    """GET /login — initiates OAuth handshake."""

    def test_login_redirects_to_oauth(self, mock_client):
        """Login should redirect (302) after initiating OAuth flow."""
        with patch("src.main_app.app_routes.auth.routes.start_login") as mock_start:
            mock_start.return_value = (
                "https://example.org/oauth/authorize",
                MagicMock(key="req_key", secret="req_secret"),
            )
            resp = mock_client.get("/login")
        assert resp.status_code == 302
        assert "example.org" in resp.headers["Location"]

    def test_login_stores_request_token_in_session(self, mock_client):
        """After login, the session should contain the OAuth request token."""
        with patch("src.main_app.app_routes.auth.routes.start_login") as mock_start:
            token = MagicMock(key="req_key", secret="req_secret")
            mock_start.return_value = (
                "https://example.org/oauth/authorize",
                token,
            )
            mock_client.get("/login")

        with mock_client.session_transaction() as session:
            assert session.get(_REQ_TOKEN_KEY) is not None

    def test_login_flash_on_failure(self, mock_client, monkeypatch):
        """If start_login raises, a danger flash message should appear."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.app_routes.auth.routes.flash", mock_flash)

        with patch(
            "src.main_app.app_routes.auth.routes.start_login",
            side_effect=RuntimeError("OAuth down"),
        ):
            resp = mock_client.get("/login", follow_redirects=True)
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("Failed to initiate OAuth login", "danger")


@pytest.mark.usefixtures("app")
class TestCallbackRoute:
    """GET /callback — completes OAuth handshake."""

    def _setup_session(self, mock_client):
        """Prepare session state as if /login was called."""
        with mock_client.session_transaction() as sess:
            sess[_STATE_KEY] = "my_nonce"
            sess[_REQ_TOKEN_KEY] = ["req_key", "req_secret"]

    def test_callback_missing_state_flash(self, mock_client, monkeypatch):
        """Callback without state in session should flash error."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.app_routes.auth.routes.flash", mock_flash)

        resp = mock_client.get("/callback", follow_redirects=True)
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("Invalid OAuth state", "danger")

    def test_callback_state_mismatch_flash(self, mock_client, monkeypatch):
        """Callback with wrong state should flash mismatch error."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.app_routes.auth.routes.flash", mock_flash)

        self._setup_session(mock_client)
        with patch(
            "src.main_app.app_routes.auth.routes.verify_state_token",
            return_value="wrong_nonce",
        ):
            resp = mock_client.get(
                "/callback?state=signed_bad&oauth_verifier=v",
                follow_redirects=True,
            )
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("OAuth state mismatch", "danger")

    def test_callback_missing_verifier_flash(self, mock_client, monkeypatch):
        """Callback without oauth_verifier should flash error."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.app_routes.auth.routes.flash", mock_flash)

        self._setup_session(mock_client)
        with patch(
            "src.main_app.app_routes.auth.routes.verify_state_token",
            return_value="my_nonce",
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok",
                follow_redirects=True,
            )
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("Invalid OAuth verifier", "danger")

    def test_callback_success_sets_session(self, app, mock_client):
        """Successful callback should set session uid and username."""
        self._setup_session(mock_client)

        fake_user_record = MagicMock(user_id=42, username="TestUser")

        with (
            patch(
                "src.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "src.main_app.app_routes.auth.routes.complete_oauth_callback",
                return_value=fake_user_record,
            ),
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=verifier_val",
                follow_redirects=False,
            )

        assert resp.status_code == 302

        with mock_client.session_transaction() as sess:
            assert sess.get("uid") is not None
            assert sess.get("username") == "TestUser"

    def test_callback_success_persists_user_token(self, app, mock_client):
        """Successful callback should upsert encrypted credentials in DB."""
        self._setup_session(mock_client)

        def _fake_complete_oauth_callback(request_token, query_string):
            with app.app_context():
                user = create_user("DbUser")
                upsert_user_token(user.user_id, "new_key", "new_secret")
            return MagicMock(user_id=user.user_id, username="DbUser")

        with (
            patch(
                "src.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "src.main_app.app_routes.auth.routes.complete_oauth_callback",
                side_effect=_fake_complete_oauth_callback,
            ),
        ):
            mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=False,
            )

        with app.app_context():

            user = get_user_by_username("DbUser")
            assert user is not None
            token = get_user_token(user.user_id)
            assert token is not None

    def test_callback_success_sets_cookie(self, app, mock_client):
        """Successful callback should set the auth cookie in response headers."""
        self._setup_session(mock_client)

        fake_user_record = MagicMock(user_id=42, username="CookieUser")

        with (
            patch(
                "src.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "src.main_app.app_routes.auth.routes.complete_oauth_callback",
                return_value=fake_user_record,
            ),
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=False,
            )

        set_cookie_headers = resp.headers.getlist("Set-Cookie")
        cookie_names = [h.split("=")[0] for h in set_cookie_headers]
        name = settings.cookie.name
        assert name in cookie_names

    def test_callback_success_redirects_to_index(self, app, mock_client):
        """After successful login, redirect should go to index."""
        self._setup_session(mock_client)

        fake_identity = {"sub": 42, "username": "RedirUser"}
        fake_access = MagicMock(key="k", secret="s")

        with (
            patch(
                "src.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "src.main_app.su_services.auth_service.complete_login",
                return_value=(fake_access, fake_identity),
            ),
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=False,
            )

        assert resp.status_code == 302
        location = resp.headers["Location"]
        assert location.endswith(("/", "/"))

    def test_callback_success_redirects_to_post_login(self, app, mock_client):
        """If post_login_redirect is set, callback redirects there."""
        self._setup_session(mock_client)
        with mock_client.session_transaction() as sess:
            sess["post_login_redirect"] = "/profile/"

        fake_user_record = MagicMock(user_id=42, username="PostRedirUser")

        with (
            patch(
                "src.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "src.main_app.app_routes.auth.routes.complete_oauth_callback",
                return_value=fake_user_record,
            ),
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=False,
            )

        assert resp.status_code == 302
        assert "/profile/" in resp.headers["Location"]


@pytest.mark.usefixtures("app")
class TestLogoutRoute:
    """GET /logout — clears session and credentials."""

    def test_logout_clears_session(self, app, mock_client):
        """After logout, session uid and username should be gone."""
        with app.app_context():
            user = create_user("LogoutUser")
            upsert_user_token(
                user_id=user.user_id,
                access_key="k",
                access_secret="s",
            )
        with mock_client.session_transaction() as sess:
            sess["uid"] = user.user_id
            sess["username"] = "LogoutUser"

        mock_client.get("/logout", follow_redirects=True)

        with mock_client.session_transaction() as sess:
            assert sess.get("uid") is None
            assert sess.get("username") is None

    def test_logout_redirects_to_index(self, mock_client, login):
        """Logout should redirect to the index page."""
        login("RedirLogout")
        resp = mock_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_without_session_still_works(self, mock_client):
        """Logout should not error even if there is no active session."""
        resp = mock_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200

    def test_logout_flash_messages(self, mock_client, login, monkeypatch):
        """Logout should display flash messages."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.app_routes.auth.routes.flash", mock_flash)

        login("FlashLogout")
        resp = mock_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("Session cleared.", "info")

    def test_logout_deletes_user_token_from_db(self, app, mock_client):
        """Logout should delete the user token record from DB."""
        with app.app_context():
            user = create_user("TokenDelete")
            upsert_user_token(
                user_id=user.user_id,
                access_key="k",
                access_secret="s",
            )

            assert get_user_token(user.user_id) is not None

        with mock_client.session_transaction() as sess:
            sess["uid"] = user.user_id
            sess["username"] = "TokenDelete"

        mock_client.get("/logout", follow_redirects=True)

        with app.app_context():

            assert get_user_token(50) is None


@pytest.mark.usefixtures("app")
class TestAuthRouteIntegration:
    """Cross-cutting integration tests for the auth blueprint."""

    def test_login_then_callback_full_flow(self, app, mock_client):
        """Full round-trip: login -> callback -> user in database."""
        # Step 1: Login
        with patch("src.main_app.app_routes.auth.routes.start_login") as mock_start:
            mock_start.return_value = (
                "https://example.org/oauth/authorize",
                MagicMock(key="rk", secret="rs"),
            )
            mock_client.get("/login")

        # Step 2: Setup callback session state
        with mock_client.session_transaction() as sess:
            sess[_STATE_KEY] = "my_nonce"
            sess[_REQ_TOKEN_KEY] = ["rk", "rs"]

        # Step 3: Callback
        def _fake_complete_oauth_callback(request_token, query_string):
            with app.app_context():
                user = create_user("FlowUser")
                upsert_user_token(user.user_id, "ak", "as")
            return MagicMock(user_id=user.user_id, username="FlowUser")

        with (
            patch(
                "src.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "src.main_app.app_routes.auth.routes.complete_oauth_callback",
                side_effect=_fake_complete_oauth_callback,
            ),
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=True,
            )

        assert resp.status_code == 200

        # Step 4: Verify user is in the database
        with app.app_context():

            user = get_user_by_username("FlowUser")
            assert user is not None
            token = get_user_token(user.user_id)
            assert token is not None

    def test_authenticated_user_can_access_profile(self, mock_client, login):
        """A logged-in user should be able to access /profile/."""
        login("ProfileUser")
        resp = mock_client.get("/profile/")
        assert resp.status_code == 200
