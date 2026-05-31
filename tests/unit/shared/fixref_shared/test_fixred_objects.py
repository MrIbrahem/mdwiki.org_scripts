"""Unit tests for flask_app/main_app/shared/fixref_shared/objects.py."""

from __future__ import annotations

from flask_app.main_app.shared.fixref_shared.objects import RunState


class TestRunStateIsolation:
    def test_each_state_starts_empty(self):
        a = RunState()
        b = RunState()
        a.from_to["X"] = "Y"
        a.normalized["P"] = "p"
        # The other state must be untouched (no shared default mutable state).
        assert b.from_to == {}
        assert b.normalized == {}


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
