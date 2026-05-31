"""Unit tests for flask_app/main_app/app_routes/newupdater/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask_app.main_app.shared.newupdater_service import newupdater_one_title


class TestWorkOnTitle:
    def test_no_user_returns_notext(self):
        result = newupdater_one_title("Test", False, user=None)
        assert result.kind == "skipped"
        assert result.msg == "No user"

    def test_empty_title_returns_notitle(self):
        result = newupdater_one_title("", False, user=MagicMock())
        assert result.kind == "skipped"
        assert result.msg == "Invalid title"

    def test_empty_title_with_spaces_returns_notext(self):
        result = newupdater_one_title("   ", False, user=MagicMock())
        assert result.kind == "skipped"
        assert result.msg == "Invalid title"
