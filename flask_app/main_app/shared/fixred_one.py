"""
Service: fix redirects in page text on mdwiki.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from ..api_services.clients.wiki_client import get_user_site
from ..su_services.users_service import current_user
from ..jobs._api import get_api
from .fixref_shared.fixred_worker import work_on_text, RunState

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
    summary: str = "Fix redirects.",
) -> UpdaterOutcome:
    """

    Returns one of:

    * ``notext``     — the page was empty or the rewriter wiped it out.
    * ``no_changes`` — the rewriter is satisfied with the current text.
    * ``changes``    — there is a diff to review/save.
    """

    user = current_user()
    site = get_user_site(user)

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

    state = RunState()
    try:
        new_text = work_on_text(api, title, old_text, site=site, state=state)
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


__all__ = [
    "work_on_title",
]
