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
from ....new_jobs.base_worker_object import BaseObjectsJobWorker
from ....shared.fixred_one import RunState
from ....shared.fixref_shared.fixred_worker import work_on_text
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)


class FixRedAllWorker(BaseObjectsJobWorker):
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

        self.result_object: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "fixred_all"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result_object.status = "failed"
            self.result_object.error = "No authenticated user site available. Please log in via OAuth."
            self.result_object.failed_at = datetime.now().isoformat()
            return self.result_object

        state = RunState()
        titles = list(
            self.site.allpages(
                start="!",
                namespace=0,
                filterredir="nonredirects",
                dir="ascending",
                generator=True,
            )
        )

        total = len(titles)
        self.result_object.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages")

        for i, page in enumerate(titles, start=1):
            logger.debug(f"i: {i}/{total}, page: {page}.")
            if self.is_cancelled():
                break

            title = page.name if hasattr(page, "name") else str(page)
            self.result_object.summary.scanned += 1

            try:
                outcome = self._process_one(title, state)
            except Exception as exc:
                logger.exception("job failed for %s", title)
                self.result_object.pages_errors.append({"title": title, "msg": str(exc)})
                continue

            self.record_page_outcome(outcome, title)

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result_object.status in ("pending", "running"):
            self.result_object.status = "completed"

        return self.result_object

    def record_page_outcome(self, outcome: UpdaterOutcome, title: str) -> None:

        page_record = {
            "title": title,
            "msg": outcome.msg,
        }
        if outcome.kind == "changed":
            page_record["newrevid"] = outcome.newrevid
            self.result_object.pages_changed.append(page_record)

        elif outcome.kind == "no_changes":
            self.result_object.pages_no_changes.append(title)

        elif outcome.kind == "missing":
            self.result_object.pages_missing.append(title)

        elif outcome.kind == "skipped":
            self.result_object.pages_skipped.append(page_record)

        elif outcome.kind == "error":
            self.result_object.pages_errors.append(page_record)

        else:
            page_record["status"] = outcome.kind
            self.result_object.pages_processed.append(page_record)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str, state: RunState) -> UpdaterOutcome:
        if not is_page_exists(title, self.site):
            return UpdaterOutcome(kind="missing")

        text = get_page_text(title, self.site)
        if not text or not text.strip():
            return UpdaterOutcome(kind="no_changes")

        new_text = work_on_text(title, text, self.site, state)
        if new_text == text:
            return UpdaterOutcome(kind="no_changes")

        summary = "Fix redirects"
        result = edit_page(self.site, title, new_text, summary)

        if result.get("success"):
            return UpdaterOutcome(kind="changed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error", msg=result.get("error", "Unknown error"))


def fixred_all_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: fixred_all")
    worker = FixRedAllWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "fixred_all_worker_entry",
]
