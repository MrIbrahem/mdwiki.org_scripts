"""Tests for the pure-text helpers in services.fixred."""

from __future__ import annotations

from main_app.services.fixred import _replace_links, _RunState


def _state(**maps) -> _RunState:
    s = _RunState()
    s.normalized.update(maps.get("normalized", {}))
    s.from_to.update(maps.get("from_to", {}))
    return s


class TestReplaceLinks:
    def test_simple_link_gets_piped_with_display_text(self):
        text = "see [[Aspirin]]."
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid", _state())
        assert result == "see [[Acetylsalicylic acid|Aspirin]]."

    def test_already_piped_link_swaps_only_the_target(self):
        text = "see [[Aspirin|the drug]]."
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid", _state())
        assert result == "see [[Acetylsalicylic acid|the drug]]."

    def test_multiple_occurrences_all_replaced(self):
        text = "[[Aspirin]] and [[Aspirin|asp]]"
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid", _state())
        assert "[[Aspirin]]" not in result
        assert "[[Aspirin|" not in result
        assert "[[Acetylsalicylic acid|Aspirin]]" in result
        assert "[[Acetylsalicylic acid|asp]]" in result

    def test_no_change_when_link_not_present(self):
        text = "no relevant links here"
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid", _state())
        assert result == text

    def test_normalized_alias_is_also_replaced(self):
        # state.normalized maps the canonical title back to the alternate
        # (e.g. lowercase) form the page text uses.
        state = _state(normalized={"Aspirin": "aspirin"})
        text = "[[aspirin]] and [[Aspirin]]"
        result = _replace_links(text, "Aspirin", "Acetylsalicylic acid", state)
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
