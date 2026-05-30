"""Unit tests for flask_app/main_app/shared/new_updater/bots/expend_new.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.bots.expend_new import expend_infoboxs


class TestExpendInfoboxs:
    def test_no_templates_returns_unchanged(self):
        text = "Plain text, no templates."
        assert expend_infoboxs(text) == text

    def test_non_infobox_template_unchanged(self):
        text = "{{Navbox|title=Test}}"
        result = expend_infoboxs(text)
        assert "Navbox" in result

    def test_infobox_drug_processed(self):
        text = "{{Infobox drug|name=Aspirin}}"
        result = expend_infoboxs(text)
        assert "Infobox drug" in result
        assert "Aspirin" in result

    def test_drugbox_processed(self):
        text = "{{drugbox|name=Test}}"
        result = expend_infoboxs(text)
        assert "drugbox" in result

    def test_empty_string(self):
        assert expend_infoboxs("") == ""
