"""Unit tests for flask_app/main_app/shared/new_updater/lists/bot_params.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.lists.bot_params import (
    all_params,
    params_placeholders,
    params_to_add,
)


class TestParamsPlaceholders:
    def test_is_dict(self):
        assert isinstance(params_placeholders, dict)

    def test_has_uses_key(self):
        assert "uses" in params_placeholders

    def test_has_side_effects_key(self):
        assert "side_effects" in params_placeholders

    def test_has_interactions_key(self):
        assert "interactions" in params_placeholders

    def test_values_are_strings(self):
        for val in params_placeholders.values():
            assert isinstance(val, str)


class TestAllParams:
    def test_is_dict(self):
        assert isinstance(all_params, dict)

    def test_has_first_key(self):
        assert "first" in all_params

    def test_has_combo_key(self):
        assert "combo" in all_params

    def test_has_names_key(self):
        assert "names" in all_params

    def test_has_clinical_key(self):
        assert "clinical" in all_params

    def test_has_legal_key(self):
        assert "legal" in all_params

    def test_has_pharmacokinetic_key(self):
        assert "pharmacokinetic" in all_params

    def test_combo_all_is_union(self):
        combo = all_params["combo"]
        all_items = combo["all"]
        assert isinstance(all_items, list)
        assert len(all_items) > 0

    def test_first_is_list_of_strings(self):
        for item in all_params["first"]:
            assert isinstance(item, str)


class TestParamsToAdd:
    def test_is_dict(self):
        assert isinstance(params_to_add, dict)

    def test_has_names_key(self):
        assert "names" in params_to_add

    def test_has_clinical_key(self):
        assert "clinical" in params_to_add

    def test_names_subset_of_all_names(self):
        for name in params_to_add["names"]:
            assert name in all_params["names"], f"{name!r} not in all_params['names']"
