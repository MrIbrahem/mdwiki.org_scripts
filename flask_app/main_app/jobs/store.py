"""Thread-safe in-memory job store.

The interface is small on purpose so a SQLite/Redis backend can be swapped
in without touching blueprints.
"""

from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import Optional

from ..config import settings
from .models import Job

JOBS_PATH: Path = Path(settings.paths.jobs_path)


class JobStore:
    """Process-local, lock-guarded :class:`Job` registry."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: dict[str, Job] = {}
        self._load_all_from_dump()

    def _load_all_from_dump(self) -> None:
        json_files = list(JOBS_PATH.glob("*.json"))
        for json_file in json_files:
            try:
                job_data = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            job = Job.from_json(job_data)
            with self._lock:
                self._jobs[job.id] = job

    def create(self, tool: str, *, submitted_by: str = "", params: Optional[dict] = None) -> Job:
        job = Job(
            id=uuid.uuid4().hex[:12],
            tool=tool,
            submitted_by=submitted_by,
            params=params or {},
        )
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def find_active(self, tool: str) -> Optional[Job]:
        """First in-flight job for the given tool, or None."""

        with self._lock:
            for job in self._jobs.values():
                if job.tool == tool and job.status in ("pending", "running"):
                    return job
        return None

    def all(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())


_store: Optional[JobStore] = None


def get_store() -> JobStore:
    """Return the process-wide :class:`JobStore` singleton."""

    global _store
    if _store is None:
        _store = JobStore()
    return _store


__all__ = ["JobStore", "get_store"]
