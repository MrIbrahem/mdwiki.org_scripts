from __future__ import annotations

import pytest
from flask_app.main_app.shared.decode_bytes import coerce_bytes


def test_coerce_bytes_bytes():
    val = b"hello"
    assert coerce_bytes(val) == val


def test_coerce_bytes_bytearray():
    val = bytearray(b"world")
    assert coerce_bytes(val) == b"world"


def test_coerce_bytes_memoryview():
    val = memoryview(b"test")
    assert coerce_bytes(val) == b"test"


def test_coerce_bytes_invalid():
    with pytest.raises(TypeError, match="Expected bytes-compatible value"):
        coerce_bytes("string")
    with pytest.raises(TypeError, match="Expected bytes-compatible value"):
        coerce_bytes(123)
