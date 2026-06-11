"""
Worker module for import_history.

Migrated from src/main_app/jobs/workers/import_history.py.
Imports revision history from English Wikipedia to mdwiki.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from mwclient.client import Site

from ....api_services import MwClientPage
from ....api_services.clients import get_user_site
from ....api_services.query_api import import_page_from_wiki
from ....jobs_workers.base_worker_object import BaseObjectsJobWorker
from .objects import ImportHistoryWorkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)


class ImportHistoryWorker(BaseObjectsJobWorker):
    """Import revision history from enwiki to mdwiki."""

    def __init__(
        self,
        job_id: int,
        args: Any,
        user: dict[str, Any] | None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args
        self.site: Site | None = None

        super().__init__(job_id, user, cancel_event)

        self.result: ImportHistoryWorkerObject = ImportHistoryWorkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "import_history"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            return self.result

        titles_raw = self.args.get("titles", [])
        from_lang = self.args.get("from_lang", "en")
        self.result.from_lang = from_lang

        if isinstance(titles_raw, str):
            titles = [t.strip() for t in titles_raw.splitlines() if t.strip()]
        else:
            titles = [t.replace("_", " ").strip() for t in titles_raw if t and t.strip()]

        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Importing history for {total} titles")

        for i, title in enumerate(titles, start=1):
            if self.is_cancelled():
                break

            self.result.summary.scanned += 1

            try:
                outcome = self._process_one(title)
            except Exception as exc:
                logger.exception("job failed for %s", title)
                self.result.pages_errors.append({"title": title, "msg": str(exc)})
                continue

            self.record_page_outcome(outcome, title)

            # Check DB if the job cancelled every N successful edits
            if outcome.kind in ("imported", "imported_fallback") and self.check_cancel_db_periodic():
                break

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    def record_page_outcome(self, outcome: UpdaterOutcome, title: str) -> None:
        page_record = {
            "title": title,
            "msg": outcome.msg,
        }
        if outcome.kind == "imported":
            page_record["newrevid"] = outcome.newrevid
            self.result.pages_imported.append(page_record)

        elif outcome.kind == "imported_fallback":
            page_record["newrevid"] = outcome.newrevid
            self.result.pages_imported_fallback.append(page_record)

        elif outcome.kind == "missing":
            self.result.pages_missing.append(title)

        elif outcome.kind == "error":
            self.result.pages_errors.append(page_record)

        else:
            page_record["status"] = outcome.kind
            self.result.pages_processed.append(page_record)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str) -> UpdaterOutcome:
        page = MwClientPage(title, self.site)
        if not page.exists():
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            return UpdaterOutcome(kind="missing")

        text = page.get_text()
        if not text or not text.strip():
            return UpdaterOutcome(kind="skipped", msg="Page is empty")

        result = import_page_from_wiki(self.site, title, family="wikipedia")
        if result.get("error"):
            logger.warning(f"Job {self.job_id}: import_page failed for {title}: {result['error']}")
            return UpdaterOutcome(kind="error", msg=result["error"])

        revisions = (result.get("import") or [{}])[0].get("revisions", 0)
        if not revisions:
            logger.info(f"Job {self.job_id}: {title!r}: import returned 0 revisions")
            return UpdaterOutcome(kind="error", msg="Import returned 0 revisions")

        logger.info(f"Job {self.job_id}: {title!r}: imported {revisions} revision(s)")

        # Re-save the original body so the page content matches what the operator
        # saw before the import.
        if text is not None:
            saved = page.edit(text, "")
            if saved.get("success"):
                return UpdaterOutcome(kind="imported", newrevid=saved.get("newrevid", 0))

            username = self.site.username or "Mr._Ibrahem"
            fallback_title = f"User:{username}/{title}"
            logger.info(f"Job {self.job_id}: {title!r}: top-level save failed; writing to {fallback_title!r}")

            fallback_result = MwClientPage(fallback_title, self.site).edit(
                text,
                "Returns the article text after importing the history",
            )

            if fallback_result.get("success"):
                return UpdaterOutcome(kind="imported_fallback", newrevid=fallback_result.get("newrevid", 0))

            logger.warning(f"Job {self.job_id}: fallback save failed too for {fallback_title}")

            return UpdaterOutcome(kind="error", msg=fallback_result.get("error", "Unknown error"))

        # return UpdaterOutcome(kind="imported")
        return UpdaterOutcome(kind="error", msg="Unknown error")


def import_history_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
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
