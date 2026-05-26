"""
Worker module for copy_svg_langs.

"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict, Iterable

import mwclient
from dataclasses import dataclass, field

from ...api_services.clients import get_user_site
from ...api_services.pages_api import edit_page, is_page_exists, is_redirect, move_page
from ..base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


@dataclass
class RenameInfo:
    """Holds the outcome of attempting to rename a single page."""

    namespace: int
    old_title: str
    new_title: str | None = None
    status: str = "pending"  # renamed | skipped_target_exists | failed
    msg: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "old_title": self.old_title,
            "new_title": self.new_title,
            "status": self.status,
            "msg": self.msg,
            "timestamp": self.timestamp,
        }


class RenameOwidPagesWorker(BaseJobWorker):
    """Background worker that capitalizes OWID subpage names."""

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
        return "copy_svg_langs"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "checked": 0,
                "to_rename": 0,
                "renamed": 0,
                "skipped_target_exists": 0,
                "redirected": 0,
                "failed": 0,
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

        # First pass: collect candidates so progress is bounded and we can
        # compute a sane save-progress interval.
        candidates: list[tuple[int, str, str, str]] = []
        for namespace, prefix, full_prefix in "PREFIXES":
            if self.is_cancelled():
                return self.result

            logger.info(f"Job {self.job_id}: Listing pages with prefix '{full_prefix}' (ns={namespace})")
            ns_count = 0
            for page in self._iter_owid_pages(namespace, prefix):
                ns_count += 1
                self.result["summary"]["checked"] += 1
                title = page.name
                yes, new_title = "needs_rename(title, full_prefix)"
                if not yes:
                    continue
                candidates.append((namespace, full_prefix, title, new_title))
                self.result["summary"]["to_rename"] += 1

            logger.info(f"Job {self.job_id}: Scanned {ns_count} page(s) under '{full_prefix}'")

        total = len(candidates)
        logger.info(f"Job {self.job_id}: {total} page(s) need renaming")

        # Save progress immediately so the UI reflects the discovery phase.
        self._save_progress()

        per_item = self.get_priority(total) if total else 1

        # Second pass: actually move.
        for n, (namespace, _full_prefix, old_title, new_title) in enumerate(candidates, start=1):
            if self.is_cancelled():
                break

            logger.info(f"Job {self.job_id}: Renaming {n}/{total}: {old_title} -> {new_title}")
            self._rename_one(namespace, old_title, new_title)

            if n == 1 or n % per_item == 0:
                self._save_progress()

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_owid_pages(self, namespace: int, prefix: str) -> Iterable:
        """Yield non-redirect pages with *prefix* in *namespace*.

        ``filterredir='nonredirects'`` means redirects left behind by previous
        runs of this job are not re-processed, keeping the job idempotent.
        """
        return self.site.allpages(
            prefix=prefix,
            namespace=namespace,
            filterredir="nonredirects",
        )

    def _rename_one(self, namespace: int, old_title: str, new_title: str) -> None:
        info = RenameInfo(namespace=namespace, old_title=old_title, new_title=new_title)

        # Pre-flight: don't even try to move if the target already exists.
        try:
            target_exists = is_page_exists(new_title, self.site)
        except Exception as exc:
            target_exists = False
            logger.exception(f"Job {self.job_id}: Failed to check existence of {new_title}", exc_info=exc)

        if target_exists:
            # Both old_title and new_title exist on the wiki.
            # Check redirect relationships to decide what to do:
            target_is_redirect = is_redirect(new_title, self.site)
            source_is_redirect = is_redirect(old_title, self.site)

            if target_is_redirect:
                # Target is a redirect (e.g. left behind by a previous move),
                # the move API will overwrite it — proceed with the move below.
                pass
            elif source_is_redirect:
                # The old page is already a redirect to the new one — just
                # update the DB title to match the capitalized version.
                info.status = "skipped_target_exists"
                info.msg = f"Old page redirects to target, updating DB only: {new_title}"
                self.result["summary"]["skipped_target_exists"] += 1
                self.result["pages_processed"].append(info.to_dict())
                return
            else:
                # Neither page redirects to the other — both are real pages.
                # Redirect the old (lowercase) page to the new (capitalized) one.
                self._redirect_old_to_new(info, old_title, new_title)
                return

        res = move_page(
            self.site,
            old_title,
            new_title,
            reason="MOVE_REASON",
            move_talk=True,
            no_redirect=False,
        )

        if res.get("success"):
            info.status = "renamed"
            info.msg = f"Moved {old_title} -> {new_title}"
            self.result["summary"]["renamed"] += 1
            # Update the title in the database
        else:
            err = res.get("error", "Unknown error")
            details = res.get("details")
            info.status = "failed"
            info.msg = f"{err}: {details}" if details else str(err)
            self.result["summary"]["failed"] += 1

        self.result["pages_processed"].append(info.to_dict())

    def _redirect_old_to_new(self, info: RenameInfo, old_title: str, new_title: str) -> None:
        """Turn the old (lowercase) page into a redirect to the new (capitalized) page."""
        redirect_text = f"#REDIRECT [[{new_title}]]"
        summary = f"Redirecting to [[{new_title}]] (capitalize first letter of OWID subpage)"

        res = edit_page(self.site, old_title, redirect_text, summary)

        if res.get("success"):
            info.status = "redirected"
            info.msg = f"Redirected {old_title} -> {new_title}"
            self.result["summary"]["redirected"] += 1
        else:
            err = res.get("error", "Unknown error")
            details = res.get("details")
            info.status = "failed"
            info.msg = f"Failed to redirect: {err}: {details}" if details else f"Failed to redirect: {err}"
            self.result["summary"]["failed"] += 1

        self.result["pages_processed"].append(info.to_dict())


def copy_svg_langs_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """
    Background worker entry-point.
    """
    logger.info(f"Starting job {job_id}: rename OWID pages (capitalize first letter)")
    worker = RenameOwidPagesWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "copy_svg_langs_worker_entry",
]
