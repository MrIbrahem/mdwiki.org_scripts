"""Unit tests for flask_app/main_app/shared/test_fixred_one.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask_app.main_app.shared.fixred_one import work_on_title
from flask_app.main_app.shared.shared_classes import UpdaterTextOutcome


class TestWorkOnTitle:
    def test_no_user_returns_notext(self):
        with patch("flask_app.main_app.shared.fixred_one.current_user", return_value=None):
            result = work_on_title("Test", False)
            assert isinstance(result, UpdaterTextOutcome)
            assert result.kind == "notext"

    def test_empty_title_returns_notext(self):
        with patch("flask_app.main_app.shared.fixred_one.current_user", return_value=MagicMock()):
            result = work_on_title("", False)
            assert result.kind == "notext"

    def test_whitespace_title_returns_notext(self):
        with patch("flask_app.main_app.shared.fixred_one.current_user", return_value=MagicMock()):
            result = work_on_title("   ", False)
            assert result.kind == "notext"
