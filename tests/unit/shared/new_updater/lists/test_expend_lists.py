"""Unit tests for flask_app/main_app/shared/new_updater/lists/expend_lists.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.lists.expend_lists import (
    IMC_params,
    dup_params,
    main_temps_list,
)


class TestMainTempsList:
    def test_is_list(self):
        assert isinstance(main_temps_list, list)

    def test_all_lowercase(self):
        for item in main_temps_list:
            assert item == item.lower(), f"Not lowercase: {item!r}"

    def test_contains_drugbox(self):
        assert "drugbox" in main_temps_list

    def test_contains_infobox_drug(self):
        assert "infobox drug" in main_temps_list

    def test_contains_infobox_medical_condition(self):
        assert "infobox medical condition" in main_temps_list

    def test_no_duplicates(self):
        assert len(main_temps_list) == len(set(main_temps_list))


class TestIMCParams:
    def test_is_dict(self):
        assert isinstance(IMC_params, dict)

    def test_infobox_medical_condition_key(self):
        assert "infobox medical condition" in IMC_params

    def test_infobox_medical_condition_new_key(self):
        assert "infobox medical condition (new)" in IMC_params

    def test_both_keys_have_same_params(self):
        assert IMC_params["infobox medical condition"] == IMC_params["infobox medical condition (new)"]

    def test_params_are_list_of_strings(self):
        for key, params in IMC_params.items():
            assert isinstance(params, list), f"{key} value is not a list"
            for p in params:
                assert isinstance(p, str), f"{key} contains non-string: {p!r}"

    def test_contains_name_param(self):
        assert "name" in IMC_params["infobox medical condition"]

    def test_contains_symptoms_param(self):
        assert "symptoms" in IMC_params["infobox medical condition"]


class TestDupParams:
    def test_is_dict(self):
        assert isinstance(dup_params, dict)

    def test_infobox_medical_condition_key(self):
        assert "infobox medical condition" in dup_params

    def test_both_keys_have_same_dup_params(self):
        assert dup_params["infobox medical condition"] == dup_params["infobox medical condition (new)"]

    def test_synonyms_maps_to_synonym(self):
        assert dup_params["infobox medical condition"]["synonyms"] == "synonym"

    def test_speciality_maps_to_field(self):
        assert dup_params["infobox medical condition"]["speciality"] == "field"
