"""
Worker module for Add unlinkedwikibase.

(TODO: import logic from https://github.com/Mdwiki-TD/mdwiki-python-files/blob/main/src/md_core/unlinked_wb/bot.py)
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from ...base_worker_object import BaseObjectsJobWorker
from ...shared_objects import SharedworkerObject

logger = logging.getLogger(__name__)


class AddUnlinkedWikibaseWorker(BaseObjectsJobWorker):
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

        self.result: SharedworkerObject = SharedworkerObject()

    def get_job_type(self) -> str:
        return "add_unlinkedwikibase"

    def process(self) -> Dict[str, Any]:
        """
        Placeholder process method.
        """
        logger.info(f"Job {self.job_id}: Placeholder for Add unlinkedwikibase processing")

        # In a real scenario, we might scan all pages.
        # For placeholder, we'll just do nothing.

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

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
