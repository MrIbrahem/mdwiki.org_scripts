"""
Worker module for fixred_all.

Migrated from flask_app/main_app/jobs/workers/fixred_all.py.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

import mwclient

from ....api_services.clients import get_user_site
from ....api_services.pages_api import edit_page, get_page_text, is_page_exists
from ....new_jobs.base_worker import BaseJobWorker
from ....shared.fixref_shared.fixred_worker import RunState, work_on_text

logger = logging.getLogger(__name__)

_NS_MAIN = 0


class FixredAllWorker(BaseJobWorker):
    """Fix redirect links in all mdwiki pages."""

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
        return "fixred_all"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "scanned": 0,
                "fixed": 0,
                "no_changes": 0,
                "missing": 0,
                "errors": 0,
                "total": 0,
            },
            "pages_processed": [],
        }

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result["status"] = "failed"
            self.result["error"] = "No authenticated user site available. Please log in via OAuth."
            self.result["failed_at"] = datetime.now().isoformat()
            return self.result

        state = RunState()
        titles = list(
            self.site.allpages(
                start="!",
                namespace=_NS_MAIN,
                filterredir="all",
                dir="ascending",
                generator=True,
            )
        )

        total = len(titles)
        self.result["summary"]["total"] = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages")

        for i, page in enumerate(titles, start=1):
            if self.is_cancelled():
                break

            title = page.name if hasattr(page, "name") else str(page)
            self.result["summary"]["scanned"] += 1

            try:
                outcome = self._treat_page(title, state)
            except Exception as exc:
                logger.exception("treat_page failed for %s", title)
                self.result["summary"]["errors"] += 1
                self.result["pages_processed"].append(
                    {
                        "title": title,
                        "status": "error",
                        "msg": str(exc),
                    }
                )
                continue

            if outcome == "fixed":
                self.result["summary"]["fixed"] += 1
            elif outcome == "no-changes":
                self.result["summary"]["no_changes"] += 1
            elif outcome == "missing":
                self.result["summary"]["missing"] += 1

            self.result["pages_processed"].append(
                {
                    "title": title,
                    "status": outcome,
                    "msg": "",
                }
            )

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _treat_page(self, title: str, state: RunState) -> str:
        """Return one of: ``missing``, ``no-changes``, ``fixed``, ``error``."""
        if not is_page_exists(title, self.site):
            return "missing"

        text = get_page_text(title, self.site)
        if text is None:
            return "missing"

        newtext = work_on_text(title, text, self.site, state)

        if newtext == text:
            return "no-changes"

        result = edit_page(self.site, title, newtext, "Fix redirects")
        if result.get("success"):
            return "fixed"
        return "error"


def fixred_all_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: fixred_all")
    worker = FixredAllWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "fixred_all_worker_entry",
]
