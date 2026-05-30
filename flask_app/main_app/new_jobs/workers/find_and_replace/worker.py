"""
Worker module for find_and_replace.

Migrated from flask_app/main_app/jobs/workers/find_and_replace.py.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

import mwclient

from ....api_services.clients import get_user_site
from ....api_services.pages_api import edit_page, get_page_text, is_page_exists

# from ....api_services.query_api import search_pages
from ....new_jobs.base_worker_object import BaseObjectsJobWorker
from ...shared_objects import UpdaterOutcome
from .objects import FindAndReplaceWorkerObject

logger = logging.getLogger(__name__)


class FindAndReplaceWorker(BaseObjectsJobWorker):
    """Find-and-replace bot for mdwiki pages."""

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

        self.result_object: FindAndReplaceWorkerObject = FindAndReplaceWorkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "find_and_replace"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result_object.status = "failed"
            self.result_object.error = "No authenticated user site available. Please log in via OAuth."
            self.result_object.failed_at = datetime.now().isoformat()
            return self.result_object

        str_find = self.args.get("str_find", "")
        str_replace = self.args.get("str_replace", "")
        listtype = self.args.get("listtype", "newlist")
        number = self.args.get("number")

        if not str_find:
            self.result_object.status = "failed"
            self.result_object.error = "`find` cannot be empty."
            return self.result_object

        self.result_object.text_find = str_find
        self.result_object.text_replace = str_replace

        try:
            cap = int(number) if number and int(number) > 0 else None
        except ValueError:
            cap = None

        self.result_object.cap = cap

        # save json file before start search
        self._save_progress()

        titles = self._resolve_titles(str_find, listtype)
        total = len(titles)
        self.result_object.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages (listtype={listtype})")

        for i, title in enumerate(titles, start=1):
            logger.debug(f"i: {i}/{total}, page: {title}.")
            if self.is_cancelled():
                self.result_object.stopped = True
                break
            if cap is not None and self.result_object.summary.changed >= cap:
                logger.info(f"Job {self.job_id}: Reached cap of {cap} modifications")
                break

            self.result_object.summary.scanned += 1

            try:
                outcome = self._process_one(title, str_find, str_replace)
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

    def _resolve_titles(
        self,
        str_find: str,
        listtype: str,
    ) -> list[str]:
        """Pick the page list to walk based on *listtype*."""
        if listtype == "newlist":
            # return search_pages(str_find, self.site, namespace=0, limit="max")
            """ """
            search_data = self.site.search(
                str_find,
                namespace="0",
                what="text",
                redirects=False,
                max_items=None,
                api_chunk_size=None,
            )
            logger.debug(search_data)
            results = [r.title for r in search_data]
            logger.info(f"Found {len(results)} pages matching '{str_find}'")
            return results

        titles = list(
            self.site.allpages(
                start="!",
                namespace=0,
                filterredir="nonredirects",
                dir="ascending",
                generator=True,
            )
        )
        # oldlist: walk every mainspace page.
        return [p.name for p in titles]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str, str_find: str, str_replace: str) -> UpdaterOutcome:
        if not is_page_exists(title, self.site):
            return UpdaterOutcome(kind="missing")

        text = get_page_text(title, self.site)
        if not text or not text.strip():
            return UpdaterOutcome(kind="no_changes")

        new_text = text.replace(str_find, str_replace)
        if new_text == text:
            return UpdaterOutcome(kind="no_changes")

        summary = "Replace via mdwiki.toolforge.org find-and-replace tool."
        result = edit_page(self.site, title, new_text, summary)

        if result.get("success"):
            return UpdaterOutcome(kind="changed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error", msg=result.get("error", "Unknown error"))


def find_and_replace_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
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
