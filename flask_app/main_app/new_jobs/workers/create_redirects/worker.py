"""
Worker module for create_redirects.

Migrated from flask_app/main_app/jobs/workers/create_redirects.py.
Copies redirects from English Wikipedia to mdwiki.
"""

from __future__ import annotations

import functools
import logging
import os
import threading
from datetime import datetime
from typing import Any, Dict

import mwclient
import requests

from ....api_services.clients import get_user_site
from ....api_services.pages_api import create_page, is_page_exists
from ....api_services.query_api import is_pages_exists
from ....new_jobs.base_worker_object import BaseObjectsJobWorker
from .objects import CreateRedirectsWorkerObject

logger = logging.getLogger(__name__)

_USER_AGENT = os.getenv(
    "REDIRECT_USER_AGENT",
    "WikiProjectMed Translation Dashboard/1.0 (https://mdwiki.toolforge.org/; tools.mdwiki@toolforge.org)",
)

_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "category:",
    "file:",
    "template:",
    "user:",
    "wikipedia:",
)


@functools.lru_cache(maxsize=1)
def _enwiki_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    return session


def _valid_title(title: str) -> bool:
    """True iff this title should be copied as a redirect on mdwiki."""
    lower = title.lower().strip()
    if "(disambiguation)" in lower:
        return False
    return not any(lower.startswith(p) for p in _FORBIDDEN_PREFIXES)


def _enwiki_redirects_for(title: str, *, timeout: int = 10) -> list[str]:
    """Mainspace redirect titles pointing to *title* on enwiki."""
    session = _enwiki_session()
    params = {
        "action": "query",
        "format": "json",
        "prop": "redirects",
        "titles": title,
        "utf8": 1,
        "rdprop": "title",
        "rdlimit": "max",
    }
    response = session.post("https://en.wikipedia.org/w/api.php", data=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json() or {}
    pages = (payload.get("query") or {}).get("pages") or {}

    out: list[str] = []

    for page in pages.values():
        for r in page.get("redirects", []) or []:
            # if page.get("title") != title: continue
            if r.get("ns") != 0:
                continue
            redirect_title = r.get("title", "")
            if redirect_title and redirect_title not in out:
                out.append(redirect_title)
    return out


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
        self.site: mwclient.Site | None = None
        self.result_object: CreateRedirectsWorkerObject = self.get_initial_result_object()
        super().__init__(job_id, user, cancel_event)

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "create_redirects"

    def get_initial_result_object(self) -> CreateRedirectsWorkerObject:
        return CreateRedirectsWorkerObject()

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result_object.status = "failed"
            self.result_object.error = "No authenticated user site available. Please log in via OAuth."
            self.result_object.failed_at = datetime.now().isoformat()
            return self.result_object

        titles_raw = self.args.get("titles", [])
        if isinstance(titles_raw, str):
            titles = [t.strip() for t in titles_raw.splitlines() if t.strip()]
        else:
            titles = [t.replace("_", " ").strip() for t in titles_raw if t and t.strip()]

        total = len(titles)
        self.result_object.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} titles")

        for i, title in enumerate(titles, start=1):
            if self.is_cancelled():
                break

            self.result_object.summary.scanned += 1

            try:
                counts = self._process_one(title)
            except Exception as exc:
                logger.exception("redirect run failed for %s", title)
                self.result_object.summary.errors += 1
                self.result_object.pages_processed.append(
                    {
                        "title": title,
                        "status": "error",
                        "msg": str(exc),
                    }
                )
                continue

            self.result_object.summary.target_missing += counts.get("target_missing", 0)
            self.result_object.summary.created += counts.get("created", 0)
            self.result_object.summary.already_exists += counts.get("already_exists", 0)
            self.result_object.summary.skipped += counts.get("skipped", 0)
            self.result_object.summary.errors += counts.get("errors", 0)

            status = "created" if counts.get("created") else "skipped"
            self.result_object.pages_processed.append(
                {
                    "title": title,
                    "status": status,
                    "msg": f"created={counts.get('created', 0)} exists={counts.get('already_exists', 0)}",
                }
            )

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result_object.status in ("pending", "running"):
            self.result_object.status = "completed"

        return self.result_object

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str) -> dict[str, int]:
        """Copy missing redirects for one source title; return per-title counts."""
        counts = {"target_missing": 0, "created": 0, "already_exists": 0, "skipped": 0, "errors": 0}

        if not is_page_exists(title, self.site):
            logger.info(f"Job {self.job_id}: target {title!r} missing on mdwiki, skipping")
            counts["target_missing"] = 1
            return counts

        redirect_titles = _enwiki_redirects_for(title)
        if not redirect_titles:
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

            result = create_page(r_title, redirect_text, self.site, summary)
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
