"""Unit tests for flask_app/main_app/utils/verify.py module."""

from __future__ import annotations

from flask_app.main_app.utils.verify import verify_required_fields


class TestVerifyRequiredFields:
    def test_all_present_returns_empty(self):
        fields = {"name": "Alice", "email": "a@b.com", "age": 30}
        assert verify_required_fields(fields) == []

    def test_missing_none(self):
        fields = {"name": "Alice", "email": None}
        result = verify_required_fields(fields)
        assert result == ["email"]

    def test_missing_empty_string(self):
        fields = {"name": "", "email": "a@b.com"}
        result = verify_required_fields(fields)
        assert result == ["name"]

    def test_missing_empty_list(self):
        fields = {"items": [], "name": "test"}
        result = verify_required_fields(fields)
        assert result == ["items"]

    def test_missing_empty_dict(self):
        fields = {"data": {}, "name": "test"}
        result = verify_required_fields(fields)
        assert result == ["data"]

    def test_missing_zero(self):
        fields = {"count": 0, "name": "test"}
        result = verify_required_fields(fields)
        assert result == ["count"]

    def test_missing_false(self):
        fields = {"flag": False, "name": "test"}
        result = verify_required_fields(fields)
        assert result == ["flag"]

    def test_multiple_missing(self):
        fields = {"a": None, "b": "", "c": 0}
        result = verify_required_fields(fields)
        assert set(result) == {"a", "b", "c"}

    def test_empty_dict_returns_empty(self):
        assert verify_required_fields({}) == []

    def test_truthy_values_pass(self):
        fields = {
            "str": "value",
            "int": 1,
            "list": [1],
            "dict": {"k": "v"},
            "bool": True,
        }
        assert verify_required_fields(fields) == []
