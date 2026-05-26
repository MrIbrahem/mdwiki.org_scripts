"""
Worker module for Add unlinkedwikibase.

(TODO: import logic from https://github.com/Mdwiki-TD/mdwiki-python-files/blob/main/src/md_core/unlinked_wb/bot.py)
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

from ....new_jobs.base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


class AddUnlinkedWikibaseWorker(BaseJobWorker):
    """Add unlinkedwikibase tag to pages."""

    def __init__(
        self,
        job_id: int,
        args: dict[str, Any] | None,
        user: dict[str, Any] | None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args or {}
        super().__init__(job_id, user, cancel_event)

    def get_job_type(self) -> str:
        return "add_unlinkedwikibase"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "scanned": 0,
                "tagged": 0,
                "skipped": 0,
                "errors": 0,
                "total": 0,
            },
            "pages_processed": [],
        }

    def process(self) -> Dict[str, Any]:
        """
        Placeholder process method.
        """
        logger.info(f"Job {self.job_id}: Placeholder for Add unlinkedwikibase processing")

        # In a real scenario, we might scan all pages.
        # For placeholder, we'll just do nothing.

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result


def add_unlinkedwikibase_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: add_unlinkedwikibase")
    worker = AddUnlinkedWikibaseWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "add_unlinkedwikibase_worker_entry",
]
