"""
Tests for the pure-text helpers in services.fixred.
"""

from __future__ import annotations

import pytest

from flask_app.main_app.public_jobs_workers.fixred import fix_text


@pytest.mark.skip(reason="fix_text is not ready yet")
def test_simple_link():
    text = """
        * [[Redirect page]]
        * [[Redirect page|test]]
        * [[ redirect page#test|redirect page]]
        * [[ redirect page # test|redirect{{!}}page]]
    """
    expected = """
        * [[Redirect testing]]
        * [[Redirect testing|test]]
        * [[ Redirect testing#test|redirect page]]
        * [[ Redirect testing # test|redirect{{!}}page]]
    """
    result = fix_text(text)
    assert result == expected
