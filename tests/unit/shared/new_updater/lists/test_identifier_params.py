"""Unit tests for flask_app/main_app/shared/new_updater/lists/identifier_params.py."""

from __future__ import annotations

from flask_app.main_app.shared.new_updater.lists.identifier_params import identifiers_params


class TestIdentifiersParams:
    def test_is_list(self):
        assert isinstance(identifiers_params, list)

    def test_not_empty(self):
        assert len(identifiers_params) > 0

    def test_all_strings(self):
        for item in identifiers_params:
            assert isinstance(item, str), f"Expected str, got {type(item)}: {item}"

    def test_contains_cas_number(self):
        assert "CAS_number" in identifiers_params

    def test_contains_pubchem(self):
        assert "PubChem" in identifiers_params

    def test_contains_drugbank(self):
        assert "DrugBank" in identifiers_params

    def test_contains_chembl(self):
        assert "ChEMBL" in identifiers_params

    def test_contains_kegg(self):
        assert "KEGG" in identifiers_params

    def test_no_duplicates(self):
        assert len(identifiers_params) == len(set(identifiers_params))

    def test_no_empty_strings(self):
        for item in identifiers_params:
            assert item.strip(), f"Empty string found at index {identifiers_params.index(item)}"
