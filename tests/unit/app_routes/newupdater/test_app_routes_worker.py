"""Unit tests for flask_app/main_app/app_routes/newupdater/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask_app.main_app.app_routes.newupdater.worker import work_on_title


class TestWorkOnTitle:
    def test_no_user_returns_notext(self):
        with patch("flask_app.main_app.app_routes.newupdater.worker.current_user", return_value=None):
            result = work_on_title("Test", False)
            assert result.kind == "skipped"
            assert result.msg == "No user"

    def test_empty_title_returns_notitle(self):
        with patch("flask_app.main_app.app_routes.newupdater.worker.current_user", return_value=MagicMock()):
            result = work_on_title("", False)
            assert result.kind == "skipped"
            assert result.msg == "Invalid title"

    def test_empty_title_with_spaces_returns_notext(self):
        with patch("flask_app.main_app.app_routes.newupdater.worker.current_user", return_value=MagicMock()):
            result = work_on_title("   ", False)
            assert result.kind == "skipped"
            assert result.msg == "Invalid title"
