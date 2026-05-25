"""Tests for services.redirect helpers."""

from __future__ import annotations

import pytest
from flask_app.main_app.public_jobs_workers.redirect import _valid_title


class TestValidTitle:
    @pytest.mark.parametrize(
        "title",
        [
            "Aspirin",
            "Crohn's disease",
            "1,2,3-Trichloropropane",
            "User:Aspirin",  # no — caught below
        ],
    )
    def test_plain_titles(self, title):
        # Pull out the User: case for negative; rest should be valid.
        if title.lower().startswith("user:"):
            assert _valid_title(title) is False
        else:
            assert _valid_title(title) is True

    @pytest.mark.parametrize(
        "title",
        [
            "Category:Drugs",
            "category:Drugs",  # case-insensitive
            "File:Pill.png",
            "Template:Drugbox",
            "User:Doc James",
            "Wikipedia:Sandbox",
        ],
    )
    def test_namespaced_titles_rejected(self, title):
        assert _valid_title(title) is False

    @pytest.mark.parametrize(
        "title",
        [
            "Aspirin (disambiguation)",
            "Apple (Disambiguation)",
        ],
    )
    def test_disambiguation_pages_rejected(self, title):
        assert _valid_title(title) is False
