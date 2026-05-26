"""Service: medical-content updater (synchronous).

In-process replacement for ``python/newupdater.py``. Unlike the other tools
this one is fast — a single page transform — so we run it inline on the
request thread instead of through the job runner.

The actual content-rewriting algorithm lives in ``python/new_updater``
(``work_on_text``). We import it via the legacy-shim path because that
module encodes years of medical-content domain rules; reimplementing it is
out of scope for the merge.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from ...shared.new_updater import work_on_text
from ...jobs._api import get_api

logger = logging.getLogger(__name__)

OutcomeKind = Literal["notext", "no_changes", "changes", "saved"]


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: OutcomeKind
    old_text: str = ""
    new_text: str = ""
    newrevid: int = 0

    @property
    def has_changes(self) -> bool:
        return self.kind == "changes"


def work_on_title(
    title: str,
    save: bool = False,
    summary: str = "Med updater.",
) -> UpdaterOutcome:
    """Fetch the page, run the updater, and report what the diff would be.

    Returns one of:

    * ``notext``     — the page was empty or the rewriter wiped it out.
    * ``no_changes`` — the rewriter is satisfied with the current text.
    * ``changes``    — there is a diff to review/save.
    """

    title = (title or "").strip()
    if not title:
        return UpdaterOutcome(kind="notext")

    api = get_api()
    page = api.MainPage(title)
    if not page.exists():
        return UpdaterOutcome(kind="notext")

    old_text = page.get_text() or ""
    if not old_text.strip():
        return UpdaterOutcome(kind="notext", old_text=old_text)

    try:
        new_text = work_on_text(title, old_text)
    except Exception:
        logger.exception("work_on_text failed for %s", title)
        raise

    if not new_text or not new_text.strip():
        return UpdaterOutcome(kind="notext", old_text=old_text)

    if new_text == old_text:
        return UpdaterOutcome(kind="no_changes", old_text=old_text, new_text=new_text)

    if save:
        ok = page.save(newtext=new_text, summary=summary)

        if ok is True:
            return UpdaterOutcome(kind="saved", newrevid=page.get_newrevid())

    return UpdaterOutcome(kind="changes", old_text=old_text, new_text=new_text)


__all__ = ["UpdaterOutcome", "work_on_title"]
