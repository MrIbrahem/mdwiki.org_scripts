"""
Worker module for find_and_replace.

"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict, Iterable

import mwclient

from ....new_jobs.base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


class FindAndReplaceWorker(BaseJobWorker):
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
        return "find_and_replace"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "scanned": 0,
                "changed": 0,
                "no_changes": 0,
                "missing": 0,
                "errors": 0,
                "total": 0,
                "stopped": False,
                "cap": None,
            },
            "pages_processed": [],
        }

    def process(self) -> Dict[str, Any]:
        # TODO: migrate logic from flask_app/main_app/jobs/workers/find_and_replace.py

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------


def find_and_replace_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """
    Background worker entry-point.
    """
    logger.info(f"Starting job {job_id}: find_and_replace")
    worker = FindAndReplaceWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "find_and_replace_worker_entry",
]
