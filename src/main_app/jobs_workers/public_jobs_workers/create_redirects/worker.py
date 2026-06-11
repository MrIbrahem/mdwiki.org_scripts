"""
Worker module for create_redirects.

Migrated from src/main_app/jobs/workers/create_redirects.py.
Copies redirects from English Wikipedia to mdwiki.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from mwclient.client import Site

from ....api_services import MwClientPage
from ....api_services.clients import get_user_site
from ....api_services.enwiki_api import get_redirects_for
from ....api_services.query_api import is_pages_exists
from ....jobs_workers.base_worker_object import BaseObjectsJobWorker
from .objects import CreateRedirectsWorkerObject

logger = logging.getLogger(__name__)

_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "category:",
    "file:",
    "template:",
    "user:",
    "wikipedia:",
)


def _valid_title(title: str) -> bool:
    """True iff this title should be copied as a redirect on mdwiki."""
    lower = title.lower().strip()
    if "(disambiguation)" in lower:
        return False
    return not any(lower.startswith(p) for p in _FORBIDDEN_PREFIXES)


class CreateRedirectsWorker(BaseObjectsJobWorker):
    """Copy redirects from enwiki to mdwiki."""

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

        self.result: CreateRedirectsWorkerObject = CreateRedirectsWorkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "create_redirects"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            return self.result

        titles = self._resolve_titles()

        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} titles")

        for i, title in enumerate(titles, start=1):
            if self.is_cancelled():
                break

            self.result.summary.scanned += 1

            try:
                counts = self._process_one(title)
            except Exception as exc:
                logger.exception("redirect run failed for %s", title)
                self.result.summary.errors += 1
                self.result.pages_errors.append({"title": title, "msg": str(exc)})
                continue

            self.result.summary.target_missing += counts.get("target_missing", 0)
            self.result.summary.created += counts.get("created", 0)
            self.result.summary.already_exists += counts.get("already_exists", 0)
            self.result.summary.skipped += counts.get("skipped", 0)
            self.result.summary.errors += counts.get("errors", 0)

            status = "created" if counts.get("created") else "skipped"

            msg = counts.get("msg") or f"created={counts.get('created', 0)} exists={counts.get('already_exists', 0)}"

            page_record = {
                "title": title,
                "status": status,
                "msg": msg,
            }

            self.result.pages_processed.append(page_record)

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    def _resolve_titles(self):
        titles_raw = self.args.get("titles", [])
        if isinstance(titles_raw, str):
            titles = [t.strip() for t in titles_raw.splitlines() if t.strip()]
        else:
            titles = [t.replace("_", " ").strip() for t in titles_raw if t and t.strip()]

        self.result.pages_to_work = titles
        return titles

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str) -> dict[str, Any]:
        """Copy missing redirects for one source title; return per-title counts."""
        counts = {"target_missing": 0, "created": 0, "already_exists": 0, "skipped": 0, "errors": 0, "msg": ""}

        page = MwClientPage(title, self.site)
        if not page.exists():
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            counts["msg"] = "target page missing"
            counts["target_missing"] = 1
            return counts

        redirect_titles = get_redirects_for(title)
        if not redirect_titles:
            counts["msg"] = "no redirects on enwiki"
            logger.info(f"Job {self.job_id}: {title!r}: no redirects on enwiki")
            return counts

        existing = is_pages_exists(redirect_titles, self.site)
        redirect_text = f"#redirect [[{title}]]"
        summary = f"Redirected page to [[{title}]]"

        for r_title, r_exists in existing.items():
            if r_exists:
                counts["already_exists"] += 1
                continue
            if not _valid_title(r_title):
                counts["skipped"] += 1
                continue

            result = MwClientPage(r_title, self.site).create(redirect_text, summary)
            if result.get("success"):
                counts["created"] += 1
                logger.info(f"Job {self.job_id}: created {r_title!r} -> {title!r}")
            else:
                counts["errors"] += 1
                logger.warning(f"Job {self.job_id}: create redirect failed: {r_title} -> {title}: {result}")

        return counts


def create_redirects_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: create_redirects")
    worker = CreateRedirectsWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "create_redirects_worker_entry",
]
