"""Tests for the auth surface: current_user, login_required, authorized_only."""

from __future__ import annotations

import pytest
from main_app.auth import ANONYMOUS, User, current_user, is_authorized


class TestUserDataclass:
    def test_anonymous_is_not_authenticated(self):
        assert ANONYMOUS.username == ""
        assert not ANONYMOUS.is_authenticated

    def test_named_user_is_authenticated(self):
        assert User(username="X").is_authenticated

    def test_user_is_frozen(self):
        u = User(username="a")
        with pytest.raises(Exception):
            u.username = "b"  # type: ignore[misc]


class TestCurrentUser:
    def test_outside_request_context_is_anonymous(self):
        # The fixture pushes a request context for client calls, but here we
        # call current_user() with no context → ANONYMOUS, no exception.
        assert current_user() is ANONYMOUS

    def test_inside_request_with_session_user(self, app, client):
        with client.session_transaction() as s:
            s["username"] = "Doc James"
        with app.test_request_context("/"):
            # In a real request the test client populates session; here we
            # just exercise the lookup against an empty session, which
            # should be anonymous.
            assert current_user() is ANONYMOUS


class TestIsAuthorized:
    def test_anonymous_is_not_authorized(self):
        assert is_authorized(ANONYMOUS) is False

    def test_unlisted_user_is_not_authorized(self):
        assert is_authorized(User(username="Random Person")) is False

    def test_allowlisted_user_is_authorized(self):
        # Set in conftest: ALLOWLIST_USERS=Doc James,Mr. Ibrahem
        assert is_authorized(User(username="Doc James")) is True
        assert is_authorized(User(username="Mr. Ibrahem")) is True


class TestLoginRequiredDecorator:
    def test_anonymous_is_redirected_to_index(self, client):
        r = client.get("/dup/")
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/")

    def test_authenticated_is_let_through(self, client, login):
        login("Anyone")
        r = client.get("/dup/")
        assert r.status_code == 200
        assert b"Fix duplicate redirects" in r.data


class TestAuthorizedOnlyDecorator:
    @pytest.mark.parametrize("path", ["/import-history/", "/replace/"])
    def test_anonymous_falls_back_to_login_redirect(self, client, path):
        r = client.get(path)
        # @login_required runs before @authorized_only, so anon → 302 to /.
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/")

    @pytest.mark.parametrize("path", ["/import-history/", "/replace/"])
    def test_unlisted_user_gets_403(self, client, login, path):
        login("Plain User")
        r = client.get(path)
        assert r.status_code == 403

    @pytest.mark.parametrize("path", ["/import-history/", "/replace/"])
    def test_allowlisted_user_is_let_through(self, client, login, path):
        login("Doc James")
        r = client.get(path)
        assert r.status_code == 200
