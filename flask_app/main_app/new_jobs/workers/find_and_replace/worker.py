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
from ....api_services.query_api import search_pages
from ....new_jobs.base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


class FindAndReplaceWorker(BaseJobWorker):
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

    # ------------------------------------------------------------------
    # BaseJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "find_and_replace"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "scanned": 0,
                "changed": 0,
                "no_changes": 0,
                "missing": 0,
                "errors": 0,
                "total": 0,
                "stopped": False,
                "cap": None,
            },
            "pages_processed": [],
        }

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result["status"] = "failed"
            self.result["error"] = "No authenticated user site available. Please log in via OAuth."
            self.result["failed_at"] = datetime.now().isoformat()
            return self.result

        find = self.args.get("find", "")
        replace = self.args.get("replace", "")
        listtype = self.args.get("listtype", "newlist")
        number = self.args.get("number")

        if not find:
            self.result["status"] = "failed"
            self.result["error"] = "`find` cannot be empty."
            return self.result

        try:
            cap = int(number) if number and int(number) > 0 else None
        except ValueError:
            cap = None

        self.result["summary"]["cap"] = cap

        titles = self._resolve_titles(find, listtype)
        total = len(titles)
        self.result["summary"]["total"] = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages (listtype={listtype})")

        for i, title in enumerate(titles, start=1):
            if self.is_cancelled():
                self.result["summary"]["stopped"] = True
                break
            if cap is not None and self.result["summary"]["changed"] >= cap:
                logger.info(f"Job {self.job_id}: Reached cap of {cap} modifications")
                break

            self.result["summary"]["scanned"] += 1

            try:
                outcome = self._process_one(title, find, replace)
            except Exception as exc:
                logger.exception("replace failed for %s", title)
                self.result["summary"]["errors"] += 1
                self.result["pages_processed"].append(
                    {
                        "title": title,
                        "status": "error",
                        "msg": str(exc),
                    }
                )
                continue

            if outcome == "changed":
                self.result["summary"]["changed"] += 1
            elif outcome == "no-changes":
                self.result["summary"]["no_changes"] += 1
            elif outcome == "missing":
                self.result["summary"]["missing"] += 1
            elif outcome == "error":
                self.result["summary"]["errors"] += 1

            self.result["pages_processed"].append(
                {
                    "title": title,
                    "status": outcome,
                    "msg": "",
                }
            )

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_titles(self, find: str, listtype: str) -> list[str]:
        """Pick the page list to walk based on *listtype*."""
        if listtype == "newlist":
            return search_pages(find, self.site, namespace=0, limit="max")
        # oldlist: walk every mainspace page.
        return [p.name for p in self.site.allpages(namespace=0)]

    def _process_one(self, title: str, find: str, replace: str) -> str:
        """Return one of: ``missing``, ``no-changes``, ``changed``, ``error``."""
        if not is_page_exists(title, self.site):
            return "missing"

        text = get_page_text(title, self.site)
        if not text or not text.strip():
            return "no-changes"

        new_text = text.replace(find, replace)
        if new_text == text:
            return "no-changes"

        summary = "Replace via mdwiki.toolforge.org find-and-replace tool."
        result = edit_page(self.site, title, new_text, summary)
        if result.get("success"):
            return "changed"
        return "error"


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
