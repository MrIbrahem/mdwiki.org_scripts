"""
Worker module for find_and_replace.

Migrated from src/main_app/jobs/workers/find_and_replace.py.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

from mwclient.client import Site

from ....api_services import MwClientPage
from ....api_services.clients import get_user_site
from ....jobs_workers.base_worker_object import BaseObjectsJobWorker
from ...shared_objects import UpdaterOutcome
from .objects import FindAndReplaceWorkerObject

# from ....api_services.query_api import search_pages

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
        self.site: Site | None = None

        super().__init__(job_id, user, cancel_event)

        self.result: FindAndReplaceWorkerObject = FindAndReplaceWorkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "find_and_replace"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            return self.result

        str_find = self.args.get("str_find", "")
        str_replace = self.args.get("str_replace", "")
        listtype = self.args.get("listtype", "newlist")
        number = self.args.get("number")

        if not str_find:
            self.result.status = "failed"
            self.result.error = "`find` cannot be empty."
            self.result.failed_at = datetime.now().isoformat()
            return self.result

        self.result.text_find = str_find
        self.result.text_replace = str_replace

        try:
            cap = int(number) if number and int(number) > 0 else None
        except ValueError:
            cap = None

        self.result.cap = cap

        # save json file before start search
        self._save_progress()

        titles = self._resolve_titles(str_find, listtype)
        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages (listtype={listtype})")

        for i, title in enumerate(titles, start=1):
            logger.debug(f"i: {i}/{total}, page: {title}.")
            if self.is_cancelled():
                self.result.stopped = True
                break

            if cap is not None and self.result.summary.changed >= cap:
                logger.info(f"Job {self.job_id}: Reached cap of {cap} modifications")
                break

            self.result.summary.scanned += 1

            try:
                outcome = self._process_one(title, str_find, str_replace)
            except Exception as exc:
                logger.exception("job failed for %s", title)
                self.result.pages_errors.append({"title": title, "msg": str(exc)})
                continue

            self.record_page_outcome(outcome, title)

            # Check DB if the job cancelled every N successful edits
            if outcome.kind == "changed" and self.check_cancel_db_periodic():
                self.result.stopped = True
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
        if outcome.kind == "changed":
            page_record["newrevid"] = outcome.newrevid
            self.result.pages_changed.append(page_record)

        elif outcome.kind == "missing":
            self.result.pages_missing.append(title)

        elif outcome.kind == "skipped":
            self.result.pages_skipped.append(page_record)

        elif outcome.kind == "error":
            self.result.pages_errors.append(page_record)

        else:
            page_record["status"] = outcome.kind
            self.result.pages_processed.append(page_record)

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
            results = [r.get("title") for r in search_data if r.get("title")]
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
        page = MwClientPage(title, self.site)
        if not page.exists():
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            return UpdaterOutcome(kind="missing")

        text = page.get_text()
        if not text or not text.strip():
            return UpdaterOutcome(kind="skipped", msg="Page is empty")

        new_text, summary = self.make_new_text(str_find, str_replace, text)

        if new_text == text:
            return UpdaterOutcome(kind="skipped", msg="No changes")

        result = page.edit(new_text, summary)

        if result.get("success"):
            return UpdaterOutcome(kind="changed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error", msg=result.get("error", "Unknown error"))

    def make_new_text(self, str_find, str_replace, text):
        new_text = text.replace(str_find, str_replace)
        summary = "Replace via mdwiki.toolforge.org find-and-replace tool."
        return new_text, summary


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
