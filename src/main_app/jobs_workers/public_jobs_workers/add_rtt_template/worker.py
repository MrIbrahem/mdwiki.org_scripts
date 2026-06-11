"""
Worker module for add_rtt_template.

Adds {{RTT}} template to all pages in Category:RTT that don't already have it.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

import wikitextparser as wtp
from mwclient.client import Site

from ....api_services import MwClientPage, get_template_pages
from ....api_services.category import get_category_members
from ....api_services.clients import get_user_site
from ....jobs_workers.base_worker_object import BaseObjectsJobWorker
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)


def add_rtt_to_text(text: str, title: str) -> str:
    new_line = "{{RTT}}"

    if text.find(new_line) != -1:
        logger.info(f"page already tagged.{new_line}")
        return text

    target_templates = ["rtt"]

    parsed = wtp.parse(text)

    for temp in parsed.templates:
        name = str(temp.normal_name()).strip().lower().replace("_", " ")
        if name in target_templates:
            logger.info(f"page already tagged.{title=}")
            return text

    newtext = text

    last_section = None

    for section in parsed.sections:
        last_section = section

    category_found = False
    if last_section:
        for line in last_section.contents.split("\n"):
            if line.strip().lower().startswith("[[category:"):
                newtext = newtext.replace(line, f"{new_line}\n{line}", 1)
                category_found = True
                break
    if not category_found:
        newtext = f"{newtext.rstrip()}\n{new_line}"

    return newtext


class AddRttTemplateWorker(BaseObjectsJobWorker):
    """Add {{RTT}} template to pages in Category:RTT."""

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

        self.result: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "add_rtt_template"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            return self.result

        mdwiki_pages = get_category_members(
            site=self.site,
            category_title="Category:RTT",
            namespace=0,
        )

        if not mdwiki_pages:
            self.result.note = "No pages in Category:RTT"
            self.result.status = "skipped"
            self.result.summary.total = 0
            self.result.summary.scanned = 0
            return self.result

        logger.info(f"Job {self.job_id}: len of mdwiki_pages: {len(mdwiki_pages)}")
        template_pages = get_template_pages(
            "Template:RTT",
            namespace=0,
            site=self.site,
        )

        logger.info(f"Job {self.job_id}: len of template_pages: {len(template_pages)}")

        pages_to_add = [x for x in mdwiki_pages if x not in template_pages]
        logger.info(f"Job {self.job_id}: len of pages_to_add: {len(pages_to_add)}")

        total = len(pages_to_add)
        if not pages_to_add:
            self.result.note = "No pages to add"
            self.result.status = "completed"
            self.result.summary.total = 0
            self.result.summary.scanned = 0
            return self.result

        self.result.summary.total = total
        self._save_progress()

        per_item = self.get_priority(total) if total else 1

        for i, title in enumerate(pages_to_add, start=1):
            logger.debug(f"i: {i}/{total}, page: {title}.")
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

            if outcome.kind == "changed" and self.check_cancel_db_periodic():
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str) -> UpdaterOutcome:
        page = MwClientPage(title, self.site)
        if not page.exists():
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            return UpdaterOutcome(kind="missing")

        ns = page.namespace
        if ns != 0:
            return UpdaterOutcome(kind="skipped", msg="Not in main namespace")

        text = page.get_text()
        if not text or not text.strip():
            return UpdaterOutcome(kind="skipped", msg="Page is empty")

        parsed = wtp.parse(text)
        if any(str(t.normal_name()).strip().lower().replace("_", " ") == "rtt" for t in parsed.templates):
            return UpdaterOutcome(kind="skipped", msg="Already has RTT template")

        new_text = add_rtt_to_text(text, title)

        if new_text == text:
            return UpdaterOutcome(kind="skipped", msg="No changes")

        result = page.edit(
            text=new_text,
            summary="Added {{RTT}}",
            nocreate=1,
        )

        if result.get("success"):
            return UpdaterOutcome(kind="changed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error", msg=result.get("error", "Unknown error"))


def add_rtt_template_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: add_rtt_template")
    worker = AddRttTemplateWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "AddRttTemplateWorker",
    "add_rtt_template_worker_entry",
]
