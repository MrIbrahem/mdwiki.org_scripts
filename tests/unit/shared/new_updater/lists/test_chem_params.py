"""Unit tests for flask_app/main_app/shared/new_updater/lists/chem_params.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.lists.chem_params import rename_chem_params


class TestRenameChemParams:
    def test_is_dict(self):
        assert isinstance(rename_chem_params, dict)

    def test_not_empty(self):
        assert len(rename_chem_params) > 0

    def test_all_keys_are_strings(self):
        for key in rename_chem_params:
            assert isinstance(key, str)

    def test_all_values_are_strings(self):
        for val in rename_chem_params.values():
            assert isinstance(val, str)

    def test_casno_maps_to_cas_number(self):
        assert rename_chem_params["CASNo"] == "CAS_number"

    def test_formula_maps_to_chemical_formula(self):
        assert rename_chem_params["Formula"] == "chemical_formula"

    def test_iupacname_maps_to_iupac_name(self):
        assert rename_chem_params["IUPACName"] == "IUPAC_name"

    def test_molarmass_maps_to_molecular_weight(self):
        assert rename_chem_params["MolarMass"] == "molecular_weight"

    def test_no_empty_keys(self):
        for key in rename_chem_params:
            assert key.strip(), f"Empty key found"

    def test_no_empty_values(self):
        for key, val in rename_chem_params.items():
            assert val.strip(), f"Empty value for key {key!r}"
