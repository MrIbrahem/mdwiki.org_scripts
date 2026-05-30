"""Unit tests for flask_app/main_app/shared/new_updater/resources_new.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.resources_new import move_resources


class TestMoveResources:
    def test_no_infobox_returns_unchanged(self):
        text = "Just plain text."
        result = move_resources(text, "Test")
        assert result == text

    def test_empty_text(self):
        result = move_resources("", "Test")
        assert result == ""

    def test_returns_string(self):
        text = "{{Infobox drug\n| name = Aspirin\n| CAS_number = 50-78-2\n}}"
        result = move_resources(text, "Aspirin")
        assert (
            result
            == """{{Infobox drug\n| name = Aspirin\n}}\n\n== External links ==\n{{drug resources\n\n<!--Identifiers-->\n| CAS_number =  50-78-2\n}}"""
        )
