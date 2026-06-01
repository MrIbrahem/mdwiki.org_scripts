"""Unit tests for flask_app/main_app/shared/new_updater/test_MedWorkNew.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.MedWorkNew import med_updater_one


class TestWorkOnText:
    def test_empty_text(self):
        result = med_updater_one("Test", "")
        assert result == ""

    def test_plain_text_no_templates(self):
        text = "Just plain text with no templates."
        result = med_updater_one("Test", text)
        assert result == "Just plain text with no templates."

    def test_preserves_content_without_infobox(self):
        text = "Some text without any medical templates."
        result = med_updater_one("Test", text)
        assert "Some text" in result
