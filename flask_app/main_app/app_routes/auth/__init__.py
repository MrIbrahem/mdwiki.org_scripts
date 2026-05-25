"""Lightweight authentication surface for blueprints.

Phase-1 scaffolding: a session-backed `current_user()` with a localhost dev
backdoor. Real OAuth wiring lands in a follow-up; only this package will need
to change at that point.
"""

from __future__ import annotations

from .current_user import ANONYMOUS, User, current_user, is_authorized

__all__ = ["ANONYMOUS", "User", "current_user", "is_authorized"]
