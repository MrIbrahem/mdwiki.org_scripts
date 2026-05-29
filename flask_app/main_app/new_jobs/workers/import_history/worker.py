"""
Worker module for import_history.

Migrated from flask_app/main_app/jobs/workers/import_history.py.
Imports revision history from English Wikipedia to mdwiki.
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
    import_page_from_wiki,
    is_page_exists,
)
from ....new_jobs.base_worker_object import BaseObjectsJobWorker
from .objects import ImportHistoryWorkerObject

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
        self.site: mwclient.Site | None = None

        super().__init__(job_id, user, cancel_event)

        self.result_object: ImportHistoryWorkerObject = ImportHistoryWorkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "import_history"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result_object.status = "failed"
            self.result_object.error = "No authenticated user site available. Please log in via OAuth."
            self.result_object.failed_at = datetime.now().isoformat()
            return self.result_object

        titles_raw = self.args.get("titles", [])
        from_lang = self.args.get("from_lang", "en")
        self.result_object.summary.from_lang = from_lang

        if isinstance(titles_raw, str):
            titles = [t.strip() for t in titles_raw.splitlines() if t.strip()]
        else:
            titles = [t.replace("_", " ").strip() for t in titles_raw if t and t.strip()]

        total = len(titles)
        self.result_object.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Importing history for {total} titles")

        for i, title in enumerate(titles, start=1):
            if self.is_cancelled():
                break

            self.result_object.summary.scanned += 1

            try:
                outcome = self._process_one(title)
            except Exception as exc:
                logger.exception("import run failed for %s", title)
                self.result_object.summary.errors += 1
                self.result_object.pages_processed.append(
                    {
                        "title": title,
                        "status": "error",
                        "msg": str(exc),
                    }
                )
                continue

            if outcome == "imported":
                self.result_object.summary.imported += 1
            elif outcome == "imported_fallback":
                self.result_object.summary.imported_fallback += 1
            elif outcome == "no_revisions":
                self.result_object.summary.no_revisions += 1
            elif outcome == "missing":
                self.result_object.summary.missing += 1
            elif outcome == "errors":
                self.result_object.summary.errors += 1

            self.result_object.pages_processed.append(
                {
                    "title": title,
                    "status": outcome,
                    "msg": "",
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

    def _process_one(self, title: str) -> str:
        """Return one of: ``missing``, ``no_revisions``, ``imported``, ``imported_fallback``, ``errors``."""
        if not is_page_exists(title, self.site):
            logger.info(f"Job {self.job_id}: {title!r}: missing on mdwiki")
            return "missing"

        text = get_page_text(title, self.site)

        result = import_page_from_wiki(self.site, title, family="wikipedia")
        if result.get("error"):
            logger.warning(f"Job {self.job_id}: import_page failed for {title}: {result['error']}")
            return "errors"

        revisions = (result.get("import") or [{}])[0].get("revisions", 0)
        if not revisions:
            logger.info(f"Job {self.job_id}: {title!r}: import returned 0 revisions")
            return "no_revisions"

        logger.info(f"Job {self.job_id}: {title!r}: imported {revisions} revision(s)")

        # Re-save the original body so the page content matches what the operator
        # saw before the import.
        if text is not None:
            saved = edit_page(self.site, title, text, "")
            if saved.get("success"):
                return "imported"

            username = self.site.username or "Mr._Ibrahem"
            fallback_title = f"User:{username}/{title}"
            logger.info(f"Job {self.job_id}: {title!r}: top-level save failed; writing to {fallback_title!r}")
            fallback_result = edit_page(
                self.site, fallback_title, text, "Returns the article text after importing the history"
            )
            if fallback_result.get("success"):
                return "imported_fallback"
            logger.warning(f"Job {self.job_id}: fallback save failed too for {fallback_title}")
            return "errors"

        return "imported"


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
