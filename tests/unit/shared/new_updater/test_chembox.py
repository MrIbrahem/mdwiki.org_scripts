"""Unit tests for flask_app/main_app/shared/new_updater/chembox.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.chembox import FixChembox


class TestFixChembox:
    def test_no_chembox_returns_unchanged(self):
        text = "Just plain text with no templates."
        bot = FixChembox(text)
        result = bot.run()
        assert result == text

    def test_chembox_converted_to_drugbox(self):
        text = "{{Chembox|Formula=C8H9NO2}}"
        bot = FixChembox(text)
        result = bot.run()
        assert "drugbox" in result.lower()

    def test_preserves_chemical_formula(self):
        text = "{{Chembox|Formula=C8H9NO2}}"
        bot = FixChembox(text)
        result = bot.run()
        assert "C8H9NO2" in result

    def test_empty_string(self):
        bot = FixChembox("")
        result = bot.run()
        assert result == ""

    def test_init_sets_text(self):
        text = "{{Chembox|test=1}}"
        bot = FixChembox(text)
        assert bot.text == text
        assert bot.new_text == text

    def test_init_empty_params(self):
        bot = FixChembox("text")
        assert bot.all_params == {}
        assert bot.oldchembox == ""
