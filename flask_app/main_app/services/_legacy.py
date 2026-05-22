"""Make the legacy `python/` text-helper packages importable.

The merge plan (`docs/merge-plan.md` §6) deliberately preserves the legacy
text-rewriting helpers — they encode years of medical-content domain rules
and re-implementing them is out of scope. The plan calls this "lift-and-shim":

* services own all *MediaWiki I/O* via `main_app.newapi.AllAPIS`;
* services delegate *text rewriting* to the legacy helpers.

Those legacy helpers were written for `pwb.py`-style invocations and use a
mix of relative and top-level imports. To make them importable from inside
the Flask app without changing them, this module appends the relevant
directories to `sys.path` once at import time.

Specifically:

* ``python/`` — so ``from new_updater import work_on_text`` resolves.
* ``python/fixref/`` — so ``from make_title_bot import make_title`` (used
  internally by ``fixref_text_new``) resolves.
* ``python/find_replace_bot/`` — for completeness; not currently needed.

Idempotent and side-effect-free beyond the path mutation.
"""

from __future__ import annotations

import sys
from pathlib import Path

# repo root is .../mdwiki.org_scripts/ — three levels up from this file
# (services/ → main_app/ → flask_app/ → repo root).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LEGACY_PYTHON = _REPO_ROOT / "python"

_LEGACY_DIRS = (
    _LEGACY_PYTHON,
    _LEGACY_PYTHON / "fixref",
    _LEGACY_PYTHON / "find_replace_bot",
)

_INSTALLED = False


def install() -> None:
    """Append the legacy directories to ``sys.path`` once."""

    global _INSTALLED
    if _INSTALLED:
        return
    for path in _LEGACY_DIRS:
        if not path.exists():
            continue
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.append(path_str)
    _INSTALLED = True


__all__ = ["install"]
