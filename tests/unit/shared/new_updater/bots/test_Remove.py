"""Unit tests for flask_app/main_app/shared/new_updater/bots/Remove.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.bots.Remove import portal_remove


class TestPortalRemove:
    def test_removes_portal_bar(self):
        text = "Some text\n{{portal bar|Medicine}}\nMore text"
        result = portal_remove(text)
        assert "portal bar" not in result
        assert "Some text" in result
        assert "More text" in result

    def test_case_insensitive(self):
        text = "{{Portal Bar|Medicine}}"
        result = portal_remove(text)
        assert "portal bar" not in result.lower()

    def test_no_portal_unchanged(self):
        text = "No portal here"
        assert portal_remove(text) == text

    def test_empty_string(self):
        assert portal_remove("") == ""

    def test_with_spaces(self):
        text = "{{ portal bar | Medicine }}"
        result = portal_remove(text)
        assert "Medicine" not in result
