"""
Worker module for fixref.

Migrated from flask_app/main_app/jobs/workers/fixref.py.
Normalizes cite-template formatting on mdwiki pages.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

import mwclient

from ....api_services.category import get_category_members_api
from ....api_services.clients import get_user_site
from ....api_services.pages_api import edit_page, get_page_text, is_page_exists
from ....shared.fixref_shared.fixref_text_new import fix_ref_template
from ...base_worker_object import BaseObjectsJobWorker
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)

MAX_PAGES_FIXREF = 20000


class FixRefWorker(BaseObjectsJobWorker):
    """Normalize references on mdwiki pages."""

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

        self.result: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "fixref"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result.status = "failed"
            self.result.error = "No authenticated user site available. Please log in via OAuth."
            self.result.failed_at = datetime.now().isoformat()
            return self.result

        titles_raw = self.args.get("titles") or self.args.get("titlelist")
        category = self.args.get("category") or self.args.get("cat")
        number = self.args.get("number")

        self._save_progress()

        pages = self._resolve_targets(titles_raw, category, number)
        if not pages:
            self.result.status = "failed"
            self.result.error = "Provide at least one of: titles, category, number."
            return self.result

        total = len(pages)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages")

        for i, title in enumerate(pages, start=1):
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

            # Check DB if the job cancelled every N successful edits
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

    def _resolve_targets(
        self,
        titles: str | list[str] | None,
        category: str | None,
        number: int | str | None,
    ) -> list[str]:
        """Resolve which pages to process given the input options."""
        if titles:
            if isinstance(titles, str):
                titles = [t.strip() for t in titles.splitlines() if t.strip()]
            cleaned: list[str] = []
            seen: set[str] = set()
            for t in titles:
                t = t.replace("_", " ").strip()
                if not t or t in seen:
                    continue
                seen.add(t)
                cleaned.append(t)
            return cleaned[:MAX_PAGES_FIXREF]

        if category:
            cat = category.strip()
            if not cat.lower().startswith("category:"):
                cat = f"Category:{cat}"
            members = get_category_members_api(cat, "www.mdwiki.org", limit=500)
            return [m for m in members if not m.startswith("Category:")][:MAX_PAGES_FIXREF]

        if number:
            try:
                capped = min(int(number), MAX_PAGES_FIXREF)
            except ValueError:
                capped = MAX_PAGES_FIXREF

            titles = list(
                self.site.allpages(
                    start="!",
                    namespace=0,
                    filterredir="nonredirects",
                    dir="ascending",
                    generator=True,
                    limit=capped,
                )
            )
            return [p.name for p in titles]

        return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str) -> UpdaterOutcome:
        if not is_page_exists(title, self.site):
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            return UpdaterOutcome(kind="missing")

        text = get_page_text(title, self.site)
        if not text or not text.strip():
            return UpdaterOutcome(kind="skipped", msg="Page is empty")

        new_text, summary = self.make_new_text(text)

        if new_text == text:
            return UpdaterOutcome(kind="skipped", msg="No changes")

        result = edit_page(self.site, title, new_text, summary)

        if result.get("success"):
            return UpdaterOutcome(kind="changed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error", msg=result.get("error", "Unknown error"))

    def make_new_text(self, text):
        new_text, summary = fix_ref_template(text, returnsummary=True)
        summary = summary or "Normalize references"
        return new_text, summary


def fixref_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: fixref")
    worker = FixRefWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "fixref_worker_entry",
]
