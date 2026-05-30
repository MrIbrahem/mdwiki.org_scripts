"""Unit tests for flask_app/main_app/shared/new_updater/helps.py module."""

from __future__ import annotations

import pytest
from flask_app.main_app.shared.new_updater.helps import ec_de_code


class TestEcDeCode:
    def test_encode(self):
        result = ec_de_code("hello world", "encode")
        assert result == "hello%20world"

    def test_decode(self):
        result = ec_de_code("hello%20world", "decode")
        assert result == "hello world"

    def test_round_trip(self):
        original = "some text with spaces & special chars"
        encoded = ec_de_code(original, "encode")
        decoded = ec_de_code(encoded, "decode")
        assert decoded == original

    def test_encode_already_safe(self):
        result = ec_de_code("hello", "encode")
        assert result == "hello"

    def test_decode_nothing_to_decode(self):
        result = ec_de_code("hello", "decode")
        assert result == "hello"

    def test_unknown_type_returns_unchanged(self):
        result = ec_de_code("hello", "unknown")
        assert result == "hello"

    def test_empty_string_encode(self):
        result = ec_de_code("", "encode")
        assert result == ""

    def test_empty_string_decode(self):
        result = ec_de_code("", "decode")
        assert result == ""

    def test_encode_unicode(self):
        result = ec_de_code("日本語", "encode")
        assert "%" in result
        decoded = ec_de_code(result, "decode")
        assert decoded == "日本語"
