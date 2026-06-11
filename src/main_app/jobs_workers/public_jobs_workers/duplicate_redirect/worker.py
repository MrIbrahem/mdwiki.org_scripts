"""
Worker module for duplicate_redirect.

Migrated from src/main_app/jobs/workers/fix_duplicate.py.

https://mdwiki.org/wiki/Special:DoubleRedirects:
WPM:Wiki Project Med/Board (redirect) → WikiProjectMed:Wiki Project Med/Board (redirect) → WikiProjectMed:Board (not redirect)

"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from mwclient.client import Site

from ....api_services import MwClientPage
from ....api_services.clients import get_user_site
from ....api_services.query_api import get_double_redirects
from ....jobs_workers.base_worker_object import BaseObjectsJobWorker
from ....shared.replace_wikilink import replace_wikilink_destinations
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)


def resolve_redirect_chains(redirects: list[dict]) -> list[dict]:
    """
    Resolves a list of redirects into a dictionary tracking the immediate
    and final targets, excluding any intermediate or final pages from the root keys.
    """
    # Create a fast lookup mapping and track all pages that are pointed 'to'
    redirect_map = {item["from"]: item["to"] for item in redirects if "from" in item and "to" in item}
    all_targets = set(redirect_map.values())

    resolved_dict = []

    # Process only the root starting pages
    for start_page in redirect_map.keys():
        if start_page in all_targets:
            continue  # Skip intermediate or final pages

        immediate_redirect = redirect_map[start_page]

        # Follow the chain to the absolute final destination
        final_target = immediate_redirect
        seen = {start_page, final_target}
        while final_target in redirect_map:
            next_target = redirect_map[final_target]
            if next_target in seen:
                break
            seen.add(next_target)
            final_target = next_target

        page_data = {
            "title": start_page,
            "redirect_to": immediate_redirect,
            "final_target": final_target,
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
        self.site: Site | None = None

        super().__init__(job_id, user, cancel_event)

        self.result: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "duplicate_redirect"

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            return self.result

        # Get all double redirects
        redirects_data = get_double_redirects(self.site)
        redirects = resolve_redirect_chains(redirects_data)

        total = len(redirects)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Loaded {len(redirects)} redirects, processing {total}")

        # for nu, (from_title, data) in enumerate(results.items(), start=1):
        for i, entry in enumerate(redirects, start=1):
            if self.is_cancelled():
                break

            # { "title": start_page, "redirect_to": immediate_redirect, "final_target": final_target }
            from_title = entry["title"]
            redirect_to = entry["redirect_to"]
            final_target = entry["final_target"]

            self.result.summary.scanned += 1

            try:
                outcome = self._process_one(from_title, redirect_to, final_target)
            except Exception as exc:
                logger.exception("job failed for %s", from_title)
                self.result.pages_errors.append(
                    {
                        "from_title": from_title,
                        "redirect_to": redirect_to,
                        "final_target": final_target,
                        "msg": str(exc),
                    }
                )
                continue

            self.record_page_outcome(outcome, entry)

            # Check DB if the job cancelled every N successful edits
            if outcome.kind == "changed" and self.check_cancel_db_periodic():
                break

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    def record_page_outcome(self, outcome: UpdaterOutcome, entry: dict[str, Any]) -> None:
        title = entry["title"]
        redirect_to = entry["redirect_to"]
        final_target = entry["final_target"]

        page_record = {
            "from_title": title,
            "redirect_to": redirect_to,
            "final_target": final_target,
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

    def _process_one(self, title: str, redirect_to: str, final_target: str) -> UpdaterOutcome:
        page = MwClientPage(title, self.site)
        if not page.exists():
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            return UpdaterOutcome(kind="missing")

        text = page.get_text()
        if not text or not text.strip():
            return UpdaterOutcome(kind="skipped", msg="Page is empty")

        new_text, summary = self.make_new_text(text, redirect_to, final_target)

        if new_text == text:
            return UpdaterOutcome(kind="skipped", msg="No changes")

        result = page.edit(new_text, summary)

        if result.get("success"):
            return UpdaterOutcome(kind="changed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error", msg=result.get("error", "Unknown error"))

    def make_new_text(self, text: str, redirect_to: str, final_target: str) -> tuple[str, str]:
        new_text = replace_wikilink_destinations(text, redirect_to, final_target)
        summary = f"fix duplicate redirect to [[{final_target}]]"

        return new_text, summary


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
