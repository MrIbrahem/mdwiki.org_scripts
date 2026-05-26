"""Background-job runner backed by a single :class:`ThreadPoolExecutor`."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any, Callable, Optional

from ..config import settings
from .models import Job
from .store import get_store

logger = logging.getLogger(__name__)

_executor: Optional[ThreadPoolExecutor] = None


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=settings.jobs.jobs_max_workers,
            thread_name_prefix="job",
        )
    return _executor


def _bump(job: Job, status: Optional[str] = None) -> None:
    job.updated_at = datetime.now(UTC)
    if status is not None:
        job.status = status

    job.dump()


def submit(
    tool: str,
    fn: Callable[..., Any],
    *,
    submitted_by: str = "",
    params: Optional[dict] = None,
    **kwargs: Any,
) -> Job:
    """Queue ``fn`` for execution under a new :class:`Job`.

    ``fn`` is invoked with two reserved kwargs:

    * ``on_progress(done: int, total: int = 0, message: str | None = None)``
    * ``stop_event: threading.Event`` — cooperative cancellation hook.

    Any extra ``**kwargs`` are forwarded verbatim to ``fn``.
    """

    store = get_store()
    job = store.create(tool, submitted_by=submitted_by, params=params or {})

    def on_progress(done: int, total: int = 0, message: Optional[str] = None) -> None:
        try:
            job.progress["done"] = int(done)
        except (TypeError, ValueError):
            pass
        if total:
            try:
                job.progress["total"] = int(total)
            except (TypeError, ValueError):
                pass
        if message:
            job.log.append(message)
        _bump(job)

    def _run() -> None:
        _bump(job, "running")
        try:
            result = fn(on_progress=on_progress, stop_event=job.stop_event, **kwargs)
            job.result = result
            _bump(job, "done")
        except Exception as exc:
            logger.exception("job %s (%s) failed", job.id, tool)
            job.error = repr(exc)
            _bump(job, "error")

    _get_executor().submit(_run)
    return job


__all__ = ["submit"]
