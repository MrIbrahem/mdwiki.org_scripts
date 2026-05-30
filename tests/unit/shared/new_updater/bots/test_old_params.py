"""Unit tests for flask_app/main_app/shared/new_updater/bots/old_params.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.bots.old_params import rename_params


class TestRenameParams:
    def test_no_templates_returns_unchanged(self):
        text = "Just plain text."
        assert rename_params(text) == text

    def test_renames_side_effects(self):
        text = "{{Infobox drug\n| side effects = headache\n}}"
        result = rename_params(text)
        assert "side_effects" in result

    def test_renames_side_effect(self):
        text = "{{Infobox drug\n| side effect = nausea\n}}"
        result = rename_params(text)
        assert "side_effects" in result

    def test_renames_legal_status(self):
        text = "{{Infobox drug\n| legal status = OTC\n}}"
        result = rename_params(text)
        assert "legal_status" in result

    def test_renames_smiles(self):
        text = "{{Infobox drug\n| smiles = CCO\n}}"
        result = rename_params(text)
        assert "SMILES" in result

    def test_non_drugbox_template_unchanged(self):
        text = "{{SomeTemplate| side effects = x }}"
        result = rename_params(text)
        assert "side effects" in result

    def test_preserves_values(self):
        text = "{{Infobox drug\n| side effects = headache\n}}"
        result = rename_params(text)
        assert "headache" in result

    def test_empty_string(self):
        assert rename_params("") == ""
