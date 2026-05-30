"""Unit tests for flask_app/main_app/shared/new_updater/bots/expend.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.bots.expend import expend_infoboxs_and_fix


class TestExpendInfoboxsAndFix:
    def test_no_templates_returns_unchanged(self):
        text = "Just some plain text with no templates."
        assert expend_infoboxs_and_fix(text) == text

    def test_non_imc_template_unchanged(self):
        text = "{{SomeOtherTemplate|param=value}}"
        result = expend_infoboxs_and_fix(text)
        assert "SomeOtherTemplate" in result

    def test_infobox_medical_condition_reformatted(self):
        text = "{{Infobox medical condition|name=Test|symptoms=Fever}}"
        result = expend_infoboxs_and_fix(text)
        assert "Infobox medical condition" in result
        assert "name" in result
        assert "symptoms" in result

    def test_preserves_content(self):
        text = "{{Infobox medical condition|name=Aspirin}}"
        result = expend_infoboxs_and_fix(text)
        assert "Aspirin" in result

    def test_empty_string(self):
        assert expend_infoboxs_and_fix("") == ""
