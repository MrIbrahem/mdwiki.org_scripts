"""Tests for the pure-text helpers in services.fixred."""

from __future__ import annotations

from flask_app.main_app.public_jobs_workers.fixred import _replace_links, _RunState


class TestReplaceLinks:
    def test_simple_link_gets_piped_with_display_text(self):
        text = "see [[Aspirin]]."
        result = _replace_links(text, "Aspirin", "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid|Aspirin]]."

    def test_already_piped_link_swaps_only_the_target(self):
        text = "see [[Aspirin|the drug]]."
        result = _replace_links(text, "Aspirin", "Aspirin", "Acetylsalicylic acid")
        assert result == "see [[Acetylsalicylic acid|the drug]]."

    def test_multiple_occurrences_all_replaced(self):
        text = "[[Aspirin]] and [[aspirin|asp]]"
        result = _replace_links(text, "Aspirin", "aspirin", "Acetylsalicylic acid")
        assert "[[Aspirin]]" not in result
        assert "[[Aspirin|" not in result
        assert "[[Acetylsalicylic acid|Aspirin]]" in result
        assert "[[Acetylsalicylic acid|asp]]" in result

    def test_no_change_when_link_not_present(self):
        text = "no relevant links here"
        result = _replace_links(text, "Aspirin", "aspirin", "Acetylsalicylic acid")
        assert result == text

    def test_normalized_alias_is_also_replaced(self):
        # state.normalized maps the canonical title back to the alternate
        # (e.g. lowercase) form the page text uses.
        text = "[[aspirin]] and [[Aspirin]]"
        result = _replace_links(text, "Aspirin", "aspirin", "Acetylsalicylic acid")
        assert "[[aspirin]]" not in result
        assert "[[Aspirin]]" not in result
        assert "[[Acetylsalicylic acid|aspirin]]" in result
        assert "[[Acetylsalicylic acid|Aspirin]]" in result


class TestRunStateIsolation:
    def test_each_state_starts_empty(self):
        a = _RunState()
        b = _RunState()
        a.from_to["X"] = "Y"
        a.normalized["P"] = "p"
        # The other state must be untouched (no shared default mutable state).
        assert b.from_to == {}
        assert b.normalized == {}
