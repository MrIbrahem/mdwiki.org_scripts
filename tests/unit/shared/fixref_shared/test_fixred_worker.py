"""Unit tests for flask_app/main_app/shared/fixref_shared/fixred_worker.py."""

from __future__ import annotations

from flask_app.main_app.shared.fixref_shared.fixred_worker import (
    RunState,
    _replace_links,
    replace_in_text,
)


class TestRunState:
    def test_default_empty(self):
        state = RunState()
        assert state.from_to == {}
        assert state.normalized == {}

    def test_mutable(self):
        state = RunState()
        state.from_to["A"] = "B"
        state.normalized["X"] = "x"
        assert state.from_to["A"] == "B"
        assert state.normalized["X"] == "x"

    def test_isolation(self):
        a = RunState()
        b = RunState()
        a.from_to["key"] = "val"
        assert b.from_to == {}


class TestReplaceLinks:
    def test_simple_link(self):
        text = "see [[Aspirin]]."
        result = _replace_links(text, "Aspirin", "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid|Aspirin]]."

    def test_piped_link(self):
        text = "see [[Aspirin|the drug]]."
        result = _replace_links(text, "Aspirin", "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid|the drug]]."

    def test_no_match(self):
        text = "no links here"
        result = _replace_links(text, "Aspirin", "aspirin", "New")
        assert result == text

    def test_normalized_alias(self):
        text = "[[aspirin]] and [[Aspirin]]"
        result = _replace_links(text, "Aspirin", "aspirin", "Acetylsalicylic acid")
        assert "[[aspirin]]" not in result
        assert "[[Aspirin]]" not in result

    def test_multiple_occurrences(self):
        text = "[[X]] and [[X|alt]]"
        result = _replace_links(text, "X", "X", "Y")
        assert "[[X]]" not in result
        assert "[[Y|X]]" in result
        assert "[[Y|alt]]" in result


class TestReplaceInText:
    def test_basic_replacement(self):
        text = "see [[Old]] page"
        result = replace_in_text(text, {"Old": "New"})
        assert "[[New|Old]]" in result

    def test_multiple_targets(self):
        text = "[[A]] and [[B]]"
        result = replace_in_text(text, {"A": "X", "B": "Y"})
        assert "[[X|A]]" in result
        assert "[[Y|B]]" in result

    def test_no_targets(self):
        text = "no changes"
        result = replace_in_text(text, {})
        assert result == text
