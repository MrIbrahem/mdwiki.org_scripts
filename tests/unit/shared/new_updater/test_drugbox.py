"""Unit tests for flask_app/main_app/shared/new_updater/drugbox.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.drugbox import TextProcessor


class TestTextProcessor:
    def test_no_drugbox_returns_empty(self):
        tp = TextProcessor("Just plain text with no templates.")
        assert tp.get_old_temp() == ""
        assert tp.get_new_temp() == ""

    def test_drugbox_detected(self):
        text = "{{Infobox drug\n| name = Aspirin\n}}"
        tp = TextProcessor(text)
        assert tp.get_old_temp() != ""

    def test_preserves_drug_name(self):
        text = "{{Infobox drug\n| name = Aspirin\n}}"
        tp = TextProcessor(text)
        new_temp = tp.get_new_temp()
        assert new_temp != ""
        assert "Aspirin" in new_temp

    def test_empty_text(self):
        tp = TextProcessor("")
        assert tp.get_old_temp() == ""
        assert tp.get_new_temp() == ""

    def test_drugbox_title_set(self):
        text = "{{Infobox drug\n| name = Test\n}}"
        tp = TextProcessor(text)
        assert tp.drugbox_title.lower() in ("infobox drug", "drugbox")

    def test_params_extracted(self):
        text = "{{Infobox drug\n| name = Aspirin\n| class = NSAID\n}}"
        tp = TextProcessor(text)
        assert "name" in tp.drugbox_params or "Aspirin" in str(tp.drugbox_params)
