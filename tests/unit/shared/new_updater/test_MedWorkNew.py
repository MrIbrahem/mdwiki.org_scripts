"""Unit tests for flask_app/main_app/shared/new_updater/test_MedWorkNew.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.MedWorkNew import work_on_text


class TestWorkOnText:
    def test_empty_text(self):
        result = work_on_text("Test", "")
        assert result == ""

    def test_plain_text_no_templates(self):
        text = "Just plain text with no templates."
        result = work_on_text("Test", text)
        assert result == ""

    def test_preserves_content_without_infobox(self):
        text = "Some text without any medical templates."
        result = work_on_text("Test", text)
        assert "Some text" in result
