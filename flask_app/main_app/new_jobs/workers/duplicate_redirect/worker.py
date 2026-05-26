"""
Worker module for duplicate_redirect.

"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict, Iterable

import mwclient

from ....new_jobs.base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


class DuplicateRedirectWorker(BaseJobWorker):
    """Background worker"""

    def __init__(
        self,
        job_id: int,
        args: Any,
        user: dict[str, Any] | None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args
        self.site: mwclient.Site | None = None
        super().__init__(job_id, user, cancel_event)

    # ------------------------------------------------------------------
    # BaseJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "duplicate_redirect"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "scanned": 0,
                "fixed": 0,
                "unchanged": 0,
                "missing": 0,
                "skipped": 0,
                "errors": 0,
                "total": 0,
            },
            "pages_processed": [],
        }

    def process(self) -> Dict[str, Any]:
        # TODO: migrate logic from flask_app/main_app/jobs/workers/fix_duplicate.py

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------


def duplicate_redirect_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """
    Background worker entry-point.
    """
    logger.info(f"Starting job {job_id}: duplicate_redirect")
    worker = DuplicateRedirectWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "duplicate_redirect_worker_entry",
]
