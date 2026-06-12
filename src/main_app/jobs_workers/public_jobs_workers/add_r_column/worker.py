"""
Worker module for Add R column.

(TODO: import logic from https://github.com/Mdwiki-TD/mdwiki-python-files/blob/main/src/md_core/add_rtt/bot.py)
"""

from __future__ import annotations

import logging
import re
import threading
from datetime import datetime
from typing import Any, Dict

import wikitextparser as wtp
from mwclient.client import Site
from mwclient.page import Page

from ....api_services import MwClientPage, get_user_site
from ....api_services.query_api import get_template_pages
from ...base_worker_object import BaseObjectsJobWorker
from .add_rtt import R_NEW_ROW, add_header_r, fix_title, header_has_r, work_one_table
from .objects import AddRColumnWorkerObject

logger = logging.getLogger(__name__)


def add_to_tables(
    text: str,
    redirects: dict,
    pages: list,
) -> str:
    parsed = wtp.parse(text)

    if not parsed.tables:
        return text

    table = parsed.tables[0]

    new_text = text

    if not header_has_r(text, table):
        new_text = add_header_r(text, table)

        if new_text == text:
            logger.info("<<red>> Can't add R column to table!")
            return text

    if redirects or pages:
        new_text = work_one_table(new_text, redirects, pages)

    table.string = new_text

    _text = parsed.string

    return _text


def get_titles_redirects(
    titles: list[str],
    site: Site,
) -> dict[str, str]:
    from_to: dict[str, str] = {}

    params = {
        # "action": "query",
        "format": "json",
        "redirects": 1,
        "utf8": 1,
        "rdlimit": "max",
    }

    for i in range(0, len(titles), 50):
        group = titles[i : i + 50]
        data = site.get("query", titles="|".join(group), **params)
        query = data.get("query", {}) or {}

        # Top-level redirects array: page is a redirect TO some target.
        for red in query.get("redirects", []) or []:
            from_to[red["from"]] = red["to"]

    return from_to


class AddRColumnWorker(BaseObjectsJobWorker):
    """Add R column to tables."""

    def __init__(
        self,
        job_id: int,
        args: dict[str, Any] | None,
        user: dict[str, Any] | None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args or {}
        self.page = None

        super().__init__(job_id, user, cancel_event)

        self.result: AddRColumnWorkerObject = AddRColumnWorkerObject()

    def get_job_type(self) -> str:
        return "add_r_column"

    def _set_step_status(self, step: str, status: str, message: str) -> None:
        self.result.set_step_status(step, status, message)

    def _set_steps_skipped(self) -> None:
        self.result.set_steps_skipped()

    def _set_status_failed(self, error) -> None:
        self.result.status = "failed"
        self.result.error = error
        self.result.failed_at = datetime.now().isoformat()

    def process(self) -> Dict[str, Any]:
        """
        process method.
        """
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            self._set_steps_skipped()
            return self.result

        logger.info(f"Job {self.job_id}: for Add R column.")

        if self.is_cancelled():
            return self.result

        self._start()

        # set any pending steps to skipped
        self._set_steps_skipped()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    def _start(self) -> bool:
        """Start the job."""
        self.result.status = "running"

        title = "WikiProjectMed:WikiProject Medicine/Popular pages"

        # step 1 load page
        self.page = MwClientPage(title, self.site)
        self._page: Page = self.page.load_page()

        if not self._page:
            self._set_step_status("load_page", "failed", "Failed to load page")
            self._set_status_failed("Failed to load page")
            return False

        if not self.page.check_exists():
            self._set_step_status("load_page", "failed", "Page does not exist")
            self._set_status_failed("Page does not exist")
            return False

        self._set_step_status("load_page", "completed", "")

        # step 2 load text
        text = ""
        try:
            text = self._page.text()
            if not text:
                raise Exception("No text")
        except Exception as exc:
            logger.exception(f"Failed to retrieve wikitext for {title}", exc_info=exc)

            self._set_step_status("load_text", "failed", "Failed to retrieve wikitext")
            self._set_status_failed("Failed to retrieve wikitext")
            return False

        self._set_step_status("load_text", "completed", "")

        # step 3 add empty R column
        try:
            new_text = add_to_tables(text, redirects={}, pages=[])
            if not new_text:
                raise Exception("No text")
        except Exception as exc:
            _err = "Failed to add empty R column to wikitext"
            logger.exception(_err, exc_info=exc)
            self._set_step_status("add_empty_r_column", "failed", _err)
            self._set_status_failed(_err)
            return False

        self._set_step_status("add_empty_r_column", "completed", "")

        if new_text != text:
            text = new_text
            """
            if not self._save_text(
                new_text,
                summary="Add R column",
                step=self.result.steps.first_save,
            ):
                self._set_status_failed("Failed to save text")
                return False
            """
        # step 4 add R column
        old_counts = text.count(R_NEW_ROW.strip())

        newtext = None
        try:
            newtext = self._newtext_step(text)
        except Exception as exc:
            logger.exception(f"Failed to add R column to {self.page.title}", exc_info=exc)

        if not newtext:
            self._set_step_status("add_r_column", "failed", "failed to render new text")
            self._set_status_failed("failed to render new text")
            return False

        self._set_step_status("add_r_column", "completed", "")

        if newtext == text:
            self.result.status = "skipped"
            self.result.error = "No changes"
            logger.info("no changes")
            return False

        # count R_NEW_ROW in newtext
        counts = newtext.count(R_NEW_ROW.strip()) - old_counts

        # step 6 save new texg to page
        summary = f"Added R column to {counts} titles."

        if not self._save_text(
            newtext,
            summary,
            step=self.result.steps.final_save,
        ):
            self.result.new_text = newtext

            self.result.steps.final_save.status = "failed"
            self.result.steps.final_save.message = "Failed to save text"

            self._set_status_failed("failed to save final text")
            return False

        return True

    def _save_text(self, new_text: str, summary: str, step) -> bool:
        saved = self.page.edit_page(text=new_text, summary=summary, nocreate=1)

        if saved.get("success"):
            step.newrevid = saved.get("newrevid", 0)
            step.status = "completed"
            return True

        logger.error(f"Failed to save text for {self.page.title}")

        error_code: str = saved.get("error", "")
        details: str = saved.get("details")
        logger.warning(f"Error code: {error_code}, details: {details}")
        return False

    def _get_text_wikilinks(self, text: str) -> list[str]:
        to_f = "== List =="

        mdwiki_pages: list[Any] = []

        if text.find(to_f) != -1:
            text = text.split(to_f)[1]
            # match all links like [[.*?]]
            pattern = r"\[\[(.*?)\]\]"
            links = re.findall(pattern, text)
            mdwiki_pages = links

        mdwiki_pages = list(set(mdwiki_pages))
        return mdwiki_pages

    def _newtext_step(self, text: str) -> str:
        # pages = CatDepth("Category:RTT", sitecode="www", family="mdwiki", depth=0, ns=0)
        template_pages = get_template_pages(
            title="Template:RTT",
            site=self.site,
            namespace=0,
        )

        links = self._get_text_wikilinks(text)
        links = [fix_title(x.strip()) for x in links if x.find("|") == -1 and x not in template_pages]

        redirects = get_titles_redirects(titles=links, site=self.site)
        newtext = add_to_tables(text, redirects, template_pages)

        return newtext


def add_r_column_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: add_r_column")
    worker = AddRColumnWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "add_r_column_worker_entry",
]
