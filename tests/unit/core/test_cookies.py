"""Unit tests for flask_app/main_app/core/cookies.py module."""

from __future__ import annotations

import pytest

from flask_app.main_app.core.cookies import CookieHeaderClient


class TestCookieHeaderClient:
    def test_class_is_subclass_of_flask_client(self):
        from flask.testing import FlaskClient
        assert issubclass(CookieHeaderClient, FlaskClient)

    def test_open_with_no_headers(self, app):
        """Calling open with no headers should not crash."""
        with app.test_client() as client:
            resp = client.get("/")
            assert resp.status_code in (200, 302, 401, 404)

    def test_open_with_dict_headers_no_cookie(self, app):
        """Dict headers without Cookie key should pass through."""
        with app.test_client() as client:
            resp = client.get("/", headers={"X-Custom": "value"})
            assert resp.status_code in (200, 302, 401, 404)

    def test_open_with_list_headers_no_cookie(self, app):
        """List-of-tuple headers without cookie should pass through."""
        with app.test_client() as client:
            resp = client.get("/", headers=[("X-Custom", "value")])
            assert resp.status_code in (200, 302, 401, 404)
