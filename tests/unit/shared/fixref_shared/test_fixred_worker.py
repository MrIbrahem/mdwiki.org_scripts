"""Unit tests for flask_app/main_app/shared/fixref_shared/fixred_worker.py."""

from __future__ import annotations

from flask_app.main_app.shared.fixref_shared.fixred_worker import (
    _replace_links,
    replace_in_text,
)


class TestReplaceLinks:
    def test_simple_link_gets_piped_with_display_text(self):
        text = "see [[Aspirin]]."
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid|Aspirin]]."

    def test_already_piped_link_swaps_only_the_target(self):
        text = "see [[Aspirin|the drug]]."
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid|the drug]]."

    def test_multiple_occurrences_all_replaced(self):
        text = "[[Aspirin]] and [[aspirin|asp]]"
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert "[[Aspirin]]" not in result
        assert "[[Aspirin|" not in result
        assert "[[Acetylsalicylic acid|Aspirin]]" in result
        assert "[[aspirin|asp]]" in result

    def test_no_change_when_link_not_present(self):
        text = "no relevant links here"
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert result == text

    def test_case_sensitive_matching(self):
        text = "[[aspirin]] and [[Aspirin]]"
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert "[[aspirin]]" in result
        assert "[[Aspirin]]" not in result
        assert "[[Acetylsalicylic acid|Aspirin]]" in result

    def test_simple_link(self):
        text = "see [[Aspirin]]."
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid|Aspirin]]."

    def test_piped_link(self):
        text = "see [[Aspirin|the drug]]."
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid|the drug]]."

    def test_no_match(self):
        text = "no links here"
        result = _replace_links(text, "Aspirin", "New")
        assert result == text

    def test_multiple_occurrences(self):
        text = "[[X]] and [[X|alt]]"
        result = _replace_links(text, "X", "Y")
        assert "[[X]]" not in result
        assert "[[Y|X]]" in result
        assert "[[Y|alt]]" in result

    def test_link_with_fragment_gets_target_replaced(self):
        text = "see [[Aspirin#Uses|the uses]]."
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid#Uses|the uses]]."

    def test_bare_link_with_fragment(self):
        text = "see [[Aspirin#Uses]]."
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid#Uses|Aspirin#Uses]]."

    def test_empty_display_text_preserved(self):
        text = "[[Aspirin|]]"
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid")
        assert result == "[[Acetylsalicylic acid|]]"

    def test_surrounding_text_preserved(self):
        text = "Before [[Aspirin]] after"
        result = _replace_links(text, "Aspirin", "New")
        assert result == "Before [[New|Aspirin]] after"

    def test_multiple_different_links_only_target_replaced(self):
        text = "[[Aspirin]] and [[Ibuprofen]]"
        result = _replace_links(text, "Aspirin", "New")
        assert "[[New|Aspirin]]" in result
        assert "[[Ibuprofen]]" in result


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
