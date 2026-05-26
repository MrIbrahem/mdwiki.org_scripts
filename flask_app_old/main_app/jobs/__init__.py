"""In-process background-job runtime.

Single-worker, in-memory by design — see ``docs/merge-plan.md`` §3.2 and §10
for the rationale and the SQLite swap-in path.
"""

from __future__ import annotations

from . import runner
from .models import Job
from .store import JobStore, get_store

__all__ = ["Job", "JobStore", "get_store", "runner"]
