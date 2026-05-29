"""
Worker module for fixref.

Migrated from flask_app/main_app/jobs/workers/fixref.py.
Normalizes cite-template formatting on mdwiki pages.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Literal

import mwclient

from ....api_services.category import get_category_members_api
from ....api_services.clients import get_user_site
from ....api_services.pages_api import edit_page, get_page_text, is_page_exists
from ....new_jobs.base_worker_object import BaseObjectsJobWorker
from ....shared.fixref_shared.fixref_text_new import fix_ref_template
from .objects import FixrefWorkerObject

logger = logging.getLogger(__name__)

MAX_PAGES_FIXREF = 20000


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: Literal["missing", "no-changes", "fixed", "error"]
    newrevid: int = 0

    @property
    def has_changes(self) -> bool:
        return self.kind == "fixed"

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


class FixrefWorker(BaseObjectsJobWorker):
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

        self.result_object: FixrefWorkerObject = FixrefWorkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "fixref"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result_object.status = "failed"
            self.result_object.error = "No authenticated user site available. Please log in via OAuth."
            self.result_object.failed_at = datetime.now().isoformat()
            return self.result_object

        titles_raw = self.args.get("titles") or self.args.get("titlelist")
        category = self.args.get("category") or self.args.get("cat")
        number = self.args.get("number")

        self._save_progress()

        pages = self._resolve_targets(titles_raw, category, number)
        if not pages:
            self.result_object.status = "failed"
            self.result_object.error = "Provide at least one of: titles, category, number."
            return self.result_object

        total = len(pages)
        self.result_object.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages")

        for i, title in enumerate(pages, start=1):
            if self.is_cancelled():
                break

            self.result_object.summary.scanned += 1

            try:
                outcome = self._process_one(title)
            except Exception as exc:
                logger.exception("fixref failed for %s", title)
                self.result_object.summary.errors += 1
                self.result_object.pages_processed.append(
                    {
                        "title": title,
                        "status": "error",
                        "msg": str(exc),
                    }
                )
                continue

            page_record = {
                "title": title,
                "status": outcome.kind,
                "msg": "",
                "newrevid": "",
            }
            if outcome.kind == "fixed":
                self.result_object.summary.fixed += 1
                page_record["newrevid"] = outcome.newrevid

            elif outcome.kind == "no-changes":
                self.result_object.summary.no_changes += 1
            elif outcome.kind == "missing":
                self.result_object.summary.missing += 1
            elif outcome.kind == "error":
                self.result_object.summary.errors += 1

            self.result_object.pages_processed.append(page_record)

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result_object.status in ("pending", "running"):
            self.result_object.status = "completed"

        return self.result_object

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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

    def _process_one(self, title: str) -> UpdaterOutcome:
        if not is_page_exists(title, self.site):
            return UpdaterOutcome(kind="missing")

        text = get_page_text(title, self.site)
        if not text or not text.strip():
            return UpdaterOutcome(kind="missing")

        new_text, summary = fix_ref_template(text, returnsummary=True)
        if not summary:
            summary = "Normalize references"

        if new_text == text:
            return UpdaterOutcome(kind="no-changes")

        result = edit_page(self.site, title, new_text, summary)
        if result.get("success"):
            return UpdaterOutcome(kind="fixed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error")


def fixref_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: fixref")
    worker = FixrefWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "fixref_worker_entry",
]
