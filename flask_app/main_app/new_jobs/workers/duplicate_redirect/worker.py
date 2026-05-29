"""
Worker module for duplicate_redirect.

Migrated from flask_app/main_app/jobs/workers/fix_duplicate.py.

https://mdwiki.org/wiki/Special:DoubleRedirects:
WPM:Wiki Project Med/Board (redirect) → WikiProjectMed:Wiki Project Med/Board (redirect) → WikiProjectMed:Board (not redirect)

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
from ...shared_objects import SharedworkerObject
from ...shared_objects import UpdaterOutcome

logger = logging.getLogger(__name__)

def resolve_redirect_chains(redirects: list[dict]) -> list[dict]:
    """
    Resolves a list of redirects into a dictionary tracking the immediate
    and final targets, excluding any intermediate or final pages from the root keys.
    """
    # Create a fast lookup mapping and track all pages that are pointed 'to'
    redirect_map = {item["from"]: item["to"] for item in redirects}
    all_targets = {item["to"] for item in redirects}

    resolved_dict = []

    # Process only the root starting pages
    for start_page in redirect_map.keys():
        if start_page in all_targets:
            continue  # Skip intermediate or final pages

        immediate_redirect = redirect_map[start_page]

        # Follow the chain to the absolute final destination
        final_target = immediate_redirect
        while final_target in redirect_map:
            final_target = redirect_map[final_target]

        page_data = {
            "title": start_page,
            "redirect_to": immediate_redirect,
            "final_target": final_target
        }
        resolved_dict.append(page_data)

    return resolved_dict


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

        super().__init__(job_id, user, cancel_event)

        self.result_object: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "duplicate_redirect"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result_object.status = "failed"
            self.result_object.error = "No authenticated user site available. Please log in via OAuth."
            self.result_object.failed_at = datetime.now().isoformat()
            return self.result_object

        # Get all double redirects
        redirects_data = get_double_redirects(self.site)
        redirects = resolve_redirect_chains(redirects_data)

        total = len(redirects)
        self.result_object.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Loaded {len(redirects)} redirects, processing {total}")

        # for nu, (from_title, data) in enumerate(results.items(), start=1):
        for i, entry in enumerate(redirects, start=1):
            if self.is_cancelled():
                break

            # { "title": start_page, "redirect_to": immediate_redirect, "final_target": final_target }
            from_title   = entry["title"]
            redirect_to  = entry["redirect_to"]
            final_target = entry["final_target"]

            self.result_object.summary.scanned += 1

            try:
                outcome = self._process_one(from_title, redirect_to, final_target)
            except Exception as exc:
                logger.exception("job failed for %s", from_title)
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

            page_record = {
                "from_title": from_title,
                "to_title": final_target,
                "status": outcome.kind,
                "msg": f"{from_title} -> {final_target}",
                "newrevid": "",
            }
            self.record_page_outcome(outcome, page_record)

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result_object.status in ("pending", "running"):
            self.result_object.status = "completed"

        return self.result_object

    def record_page_outcome(self, outcome, page_record):
        if outcome.kind == "changed":
            self.result_object.summary.changed += 1
            page_record["newrevid"] = outcome.newrevid

        elif outcome.kind == "no_changes":
            self.result_object.summary.no_changes += 1
        elif outcome.kind == "missing":
            self.result_object.summary.missing += 1
        elif outcome.kind == "error":
            self.result_object.summary.errors += 1

        self.result_object.pages_processed.append(page_record)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str, redirect_to: str, final_target: str) -> UpdaterOutcome:
        """
        Treat one double redirect; return a short outcome label.
        """
        if not is_page_exists(title, self.site):
            return UpdaterOutcome(kind="missing")

        text = get_page_text(title, self.site) or ""

        # TODO: replace only the link not the whole text, use wikitextparser to analyze the text
        new_text = f"#REDIRECT [[{final_target}]]"

        if new_text == text:
            return UpdaterOutcome(kind="no_changes")

        summary = f"fix duplicate redirect to [[{final_target}]]"

        result = edit_page(self.site, title, new_text, summary)
        if result.get("success"):
            return UpdaterOutcome(kind="changed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error")


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
