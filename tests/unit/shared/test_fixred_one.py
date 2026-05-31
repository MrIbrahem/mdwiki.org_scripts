"""Unit tests for flask_app/main_app/shared/test_fixred_one.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from flask_app.main_app.shared.fixred_one import work_on_title
from flask_app.main_app.shared.shared_classes import UpdaterTextOutcome


class TestWorkOnTitle:
    def test_no_user_returns_notext(self):
        result = work_on_title("Test", False, user=None)
        assert isinstance(result, UpdaterTextOutcome)
        assert result.kind == "skipped"
        assert result.msg == "No user"

    def test_empty_title_returns_notitle(self):
        result = work_on_title("", False, user=MagicMock())
        assert result.kind == "skipped"
        assert result.msg == "Invalid title"

    def test_whitespace_title_returns_notext(self):
        result = work_on_title("   ", False, user=MagicMock())
        assert result.kind == "skipped"
        assert result.msg == "Invalid title"
