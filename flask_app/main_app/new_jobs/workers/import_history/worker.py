"""
Worker module for import_history.

"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict, Iterable

import mwclient

from ....new_jobs.base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


class ImportHistoryWorker(BaseJobWorker):
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
        return "import_history"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "scanned": 0,
                "imported": 0,
                "imported_fallback": 0,
                "no_revisions": 0,
                "missing": 0,
                "errors": 0,
                "total": 0,
                "from_lang": "en",
            },
            "pages_processed": [],
        }

    def process(self) -> Dict[str, Any]:
        # TODO: migrate logic from flask_app/main_app/jobs/workers/import_history.py

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------


def import_history_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """
    Background worker entry-point.
    """
    logger.info(f"Starting job {job_id}: import_history")
    worker = ImportHistoryWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "import_history_worker_entry",
]
