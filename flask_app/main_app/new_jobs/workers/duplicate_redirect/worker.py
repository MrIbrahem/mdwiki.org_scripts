"""
Worker module for duplicate_redirect.

Migrated from flask_app/main_app/jobs/workers/fix_duplicate.py.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

import mwclient

from ....api_services.clients import get_user_site
from ....api_services.pages_api import (
    edit_page,
    get_page_text,
    is_page_exists,
)
from ....api_services.query_api import get_double_redirects
from ....new_jobs.base_worker_object import BaseObjectsJobWorker
from .objects import DuplicateRedirectWorkerObject

logger = logging.getLogger(__name__)


class DuplicateRedirectWorker(BaseObjectsJobWorker):
    """Fix double redirects on mdwiki."""

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
        self.result_object: DuplicateRedirectWorkerObject = self.get_initial_result_object()
        super().__init__(job_id, user, cancel_event)

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "duplicate_redirect"

    def get_initial_result_object(self) -> DuplicateRedirectWorkerObject:
        return DuplicateRedirectWorkerObject()

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result_object.status = "failed"
            self.result_object.error = "No authenticated user site available. Please log in via OAuth."
            self.result_object.failed_at = datetime.now().isoformat()
            return self.result_object

        # Get all double redirects
        redirects = get_double_redirects(self.site)
        from_to = {e["from"]: e["to"] for e in redirects if "from" in e and "to" in e}

        total = len(redirects)
        self.result_object.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Loaded {len(redirects)} redirects, processing {total}")

        for i, entry in enumerate(redirects, start=1):
            if self.is_cancelled():
                break

            from_title = entry.get("from", "")
            intermediate = entry.get("to", "")
            seen = {from_title, intermediate}
            curr = intermediate
            while curr in from_to:
                next_target = from_to[curr]
                if next_target in seen:
                    break
                seen.add(next_target)
                curr = next_target
            final_target = curr

            self.result_object.summary.scanned += 1

            if not from_title or not final_target:
                self.result_object.summary.skipped += 1
                self.result_object.pages_processed.append(
                    {
                        "from_title": from_title,
                        "to_title": final_target,
                        "status": "skipped",
                        "msg": "not a double redirect",
                    }
                )
                continue

            try:
                outcome = self._fix_one(from_title, final_target)
            except Exception as exc:
                logger.exception("failed for %s -> %s", from_title, final_target)
                self.result_object.summary.errors += 1
                self.result_object.pages_processed.append(
                    {
                        "from_title": from_title,
                        "to_title": final_target,
                        "status": "error",
                        "msg": str(exc),
                    }
                )
                continue

            if outcome == "fixed":
                self.result_object.summary.fixed += 1
            elif outcome == "unchanged":
                self.result_object.summary.unchanged += 1
            elif outcome == "missing":
                self.result_object.summary.missing += 1
            elif outcome == "errors":
                self.result_object.summary.errors += 1

            self.result_object.pages_processed.append(
                {
                    "from_title": from_title,
                    "to_title": final_target,
                    "status": outcome,
                    "msg": f"{from_title} -> {final_target}",
                }
            )

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result_object.status in ("pending", "running"):
            self.result_object.status = "completed"

        return self.result_object

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fix_one(self, from_title: str, final_target: str) -> str:
        """Treat one double redirect; return a short outcome label."""
        if not is_page_exists(from_title, self.site):
            return "missing"

        oldtext = get_page_text(from_title, self.site) or ""
        newtext = f"#REDIRECT [[{final_target}]]"

        if oldtext == newtext:
            return "unchanged"

        summary = f"fix duplicate redirect to [[{final_target}]]"
        result = edit_page(self.site, from_title, newtext, summary)
        if result.get("success"):
            return "fixed"
        return "errors"


def duplicate_redirect_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
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
