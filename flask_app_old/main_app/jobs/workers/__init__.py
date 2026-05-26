"""Service layer.

Each module in this package is the in-process replacement for one of the
legacy CLI scripts in ``python/<tool>.py``. Services expose ``run(...)``
functions that take primitives, return a result dict, and are safe to call
from a worker thread.

See ``docs/merge-plan.md`` §3.1 (layering) and §6 (refactor strategy).
"""

from __future__ import annotations

__all__: list[str] = []
