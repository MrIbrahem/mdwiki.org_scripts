"""Integration tests for flask_app/main_app/app_routes/auth/routes.py module.

Tests the full OAuth login/logout flow through the Flask test client with
a real SQLite database (via TestingConfig). OAuth external calls are stubbed
so no network access is required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from flask_app.main_app.db.services import delete_user_token, upsert_user_token


def _seed_user(app, user_id=42, username="TestUser"):
    """Insert a user token record into the database."""
    with app.app_context():
        upsert_user_token(
            user_id=user_id,
            username=username,
            access_key="fake-key",
            access_secret="fake-secret",
        )


@pytest.mark.usefixtures("app")
class TestLoginRoute:
    """GET /login — initiates OAuth handshake."""

    def test_login_redirects_to_oauth(self, mock_client):
        """Login should redirect (302) after initiating OAuth flow."""
        with patch(
            "flask_app.main_app.app_routes.auth.routes.start_login"
        ) as mock_start:
            mock_start.return_value = (
                "https://example.org/oauth/authorize",
                MagicMock(key="req_key", secret="req_secret"),
            )
            resp = mock_client.get("/login")
        assert resp.status_code == 302
        assert "example.org" in resp.headers["Location"]

    def test_login_stores_request_token_in_session(self, mock_client):
        """After login, the session should contain the OAuth request token."""
        with patch(
            "flask_app.main_app.app_routes.auth.routes.start_login"
        ) as mock_start:
            token = MagicMock(key="req_key", secret="req_secret")
            mock_start.return_value = (
                "https://example.org/oauth/authorize",
                token,
            )
            mock_client.get("/login")

        with mock_client.session_transaction() as session:
            assert session.get("request_token") is not None

    def test_login_flash_on_failure(self, mock_client):
        """If start_login raises, a danger flash message should appear."""
        with patch(
            "flask_app.main_app.app_routes.auth.routes.start_login",
            side_effect=RuntimeError("OAuth down"),
        ):
            resp = mock_client.get("/login", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Failed to initiate OAuth login" in resp.data


@pytest.mark.usefixtures("app")
class TestCallbackRoute:
    """GET /callback — completes OAuth handshake."""

    def _setup_session(self, mock_client):
        """Prepare session state as if /login was called."""
        with mock_client.session_transaction() as sess:
            sess["oauth_state"] = "my_nonce"
            sess["request_token"] = ["req_key", "req_secret"]

    def test_callback_missing_state_flash(self, mock_client):
        """Callback without state in session should flash error."""
        resp = mock_client.get("/callback", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Invalid OAuth state" in resp.data

    def test_callback_state_mismatch_flash(self, mock_client):
        """Callback with wrong state should flash mismatch error."""
        self._setup_session(mock_client)
        with patch(
            "flask_app.main_app.app_routes.auth.routes.verify_state_token",
            return_value="wrong_nonce",
        ):
            resp = mock_client.get(
                "/callback?state=signed_bad&oauth_verifier=v",
                follow_redirects=True,
            )
        assert resp.status_code == 200
        assert b"OAuth state mismatch" in resp.data

    def test_callback_missing_verifier_flash(self, mock_client):
        """Callback without oauth_verifier should flash error."""
        self._setup_session(mock_client)
        with patch(
            "flask_app.main_app.app_routes.auth.routes.verify_state_token",
            return_value="my_nonce",
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok",
                follow_redirects=True,
            )
        assert resp.status_code == 200
        assert b"Invalid OAuth verifier" in resp.data

    def test_callback_success_sets_session(self, app, mock_client):
        """Successful callback should set session uid and username."""
        self._setup_session(mock_client)

        fake_identity = {"sub": 42, "username": "TestUser"}
        fake_access = MagicMock(key="acc_key", secret="acc_secret")

        with (
            patch(
                "flask_app.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "flask_app.main_app.app_routes.auth.routes.complete_login",
                return_value=(fake_access, fake_identity),
            ),
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=verifier_val",
                follow_redirects=False,
            )

        assert resp.status_code == 302

        with mock_client.session_transaction() as sess:
            assert sess.get("uid") == 42
            assert sess.get("username") == "TestUser"

    def test_callback_success_persists_user_token(self, app, mock_client):
        """Successful callback should upsert encrypted credentials in DB."""
        self._setup_session(mock_client)

        fake_identity = {"sub": 99, "username": "DbUser"}
        fake_access = MagicMock(key="new_key", secret="new_secret")

        with (
            patch(
                "flask_app.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "flask_app.main_app.app_routes.auth.routes.complete_login",
                return_value=(fake_access, fake_identity),
            ),
        ):
            mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=False,
            )

        with app.app_context():
            from flask_app.main_app.db.services import get_user_token

            user = get_user_token(99)
            assert user is not None
            assert user.username == "DbUser"

    def test_callback_success_sets_cookie(self, app, mock_client):
        """Successful callback should set the auth cookie."""
        self._setup_session(mock_client)

        fake_identity = {"sub": 42, "username": "CookieUser"}
        fake_access = MagicMock(key="k", secret="s")

        with (
            patch(
                "flask_app.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "flask_app.main_app.app_routes.auth.routes.complete_login",
                return_value=(fake_access, fake_identity),
            ),
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=False,
            )

        from flask_app.main_app.config import settings

        assert settings.cookie.name in resp.headers.get("Set-Cookie", "")

    def test_callback_success_redirects_to_index(self, app, mock_client):
        """After successful login, redirect should go to index (no post_login_redirect)."""
        self._setup_session(mock_client)

        fake_identity = {"sub": 42, "username": "RedirUser"}
        fake_access = MagicMock(key="k", secret="s")

        with (
            patch(
                "flask_app.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "flask_app.main_app.app_routes.auth.routes.complete_login",
                return_value=(fake_access, fake_identity),
            ),
        ):
            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=False,
            )

        assert resp.status_code == 302
        assert resp.headers["Location"] in ("/", "http://localhost/")

    def test_callback_success_redirects_to_post_login(self, app, mock_client):
        """If post_login_redirect is set, callback redirects there."""
        self._setup_session(mock_client)
        with mock_client.session_transaction() as sess:
            sess["post_login_redirect"] = "/profile/"

        fake_identity = {"sub": 42, "username": "PostRedirUser"}
        fake_access = MagicMock(key="k", secret="s")

        with (
            patch(
                "flask_app.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "flask_app.main_app.app_routes.auth.routes.complete_login",
                return_value=(fake_access, fake_identity),
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

    def test_logout_clears_session(self, mock_client, login):
        """After logout, session uid and username should be gone."""
        login("LogoutUser")
        _seed_user(
            pytest.importorskip("flask").current_app._get_current_object()
            if False
            else None,
            user_id=42,
            username="LogoutUser",
        )
        # Use a separate app context for seeding
        from flask import current_app

        with current_app.app_context():
            upsert_user_token(
                user_id=42,
                username="LogoutUser",
                access_key="k",
                access_secret="s",
            )

        mock_client.get("/logout", follow_redirects=True)

        with mock_client.session_transaction() as sess:
            assert sess.get("uid") is None
            assert sess.get("username") is None

    def test_logout_deletes_auth_cookie(self, mock_client, login):
        """Logout should delete the auth cookie."""
        login("CookieLogout")
        resp = mock_client.get("/logout", follow_redirects=False)
        cookie_header = resp.headers.get("Set-Cookie", "")
        from flask_app.main_app.config import settings

        assert settings.cookie.name in cookie_header

    def test_logout_redirects_to_index(self, mock_client, login):
        """Logout should redirect to the index page."""
        login("RedirLogout")
        resp = mock_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_without_session_still_works(self, mock_client):
        """Logout should not error even if there is no active session."""
        resp = mock_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200

    def test_logout_flash_messages(self, mock_client, login):
        """Logout should display flash messages."""
        login("FlashLogout")
        resp = mock_client.get("/logout", follow_redirects=True)
        assert b"Logout successful" in resp.data


@pytest.mark.usefixtures("app")
class TestAuthRouteIntegration:
    """Cross-cutting integration tests for the auth blueprint."""

    def test_login_then_callback_full_flow(self, app, mock_client):
        """Full round-trip: login -> callback -> authenticated request."""
        # Step 1: Login
        with patch(
            "flask_app.main_app.app_routes.auth.routes.start_login"
        ) as mock_start:
            mock_start.return_value = (
                "https://example.org/oauth/authorize",
                MagicMock(key="rk", secret="rs"),
            )
            mock_client.get("/login")

        # Step 2: Callback
        fake_identity = {"sub": 77, "username": "FlowUser"}
        fake_access = MagicMock(key="ak", secret="as")

        with (
            patch(
                "flask_app.main_app.app_routes.auth.routes.verify_state_token",
                return_value="my_nonce",
            ),
            patch(
                "flask_app.main_app.app_routes.auth.routes.complete_login",
                return_value=(fake_access, fake_identity),
            ),
        ):
            # Set up session state from step 1
            with mock_client.session_transaction() as sess:
                sess["oauth_state"] = "my_nonce"
                sess["request_token"] = ["rk", "rs"]

            resp = mock_client.get(
                "/callback?state=signed_ok&oauth_verifier=v",
                follow_redirects=True,
            )

        assert resp.status_code == 200

        # Step 3: Verify user is in the database
        with app.app_context():
            from flask_app.main_app.db.services import get_user_token

            user = get_user_token(77)
            assert user is not None
            assert user.username == "FlowUser"

    def test_authenticated_user_can_access_profile(self, mock_client, login):
        """A logged-in user should be able to access /profile/."""
        login("ProfileUser")
        resp = mock_client.get("/profile/")
        assert resp.status_code == 200

    def test_unauthenticated_user_redirected_from_fixred(self, mock_client):
        """An unauthenticated user should be redirected from /fixred/."""
        resp = mock_client.get("/fixred/")
        assert resp.status_code in (302, 401, 403)
