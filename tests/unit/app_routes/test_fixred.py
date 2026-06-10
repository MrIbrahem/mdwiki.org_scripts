"""Unit tests for src/main_app/app_routes/fixred.py module."""

from __future__ import annotations

import pytest

from src.main_app.app_routes.fixred import _normalize_title


class TestNormalizeTitle:
    def test_replaces_underscores(self):
        assert _normalize_title("Aspirin_Tablet") == "Aspirin Tablet"

    def test_strips_whitespace(self):
        assert _normalize_title("  Aspirin  ") == "Aspirin"

    def test_empty_string(self):
        assert _normalize_title("") == ""

    def test_none_input(self):
        assert _normalize_title(None) == ""

    def test_already_normalized(self):
        assert _normalize_title("Aspirin") == "Aspirin"

    def test_multiple_underscores(self):
        assert _normalize_title("Some_Long_Page_Name") == "Some Long Page Name"

    def test_leading_underscores_stripped_after_replace(self):
        # "_Aspirin_" -> after replace: " Aspirin " -> after strip: "Aspirin"
        assert _normalize_title("_Aspirin_") == "Aspirin"


@pytest.mark.usefixtures("app")
class TestFixredRoutes:
    """Tests for the fixred blueprint routes."""

    def test_get_index_requires_auth(self, mock_client):
        resp = mock_client.get("/fixred/")
        # oauth_required redirects unauthenticated users to login
        assert resp.status_code == 302

    def test_post_index_requires_auth(self, mock_client):
        resp = mock_client.post("/fixred/", data={"title": "Test"})
        assert resp.status_code == 302
