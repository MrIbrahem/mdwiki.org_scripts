"""
Service: fix redirects in page text on mdwiki.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from ..api_services.clients.wiki_client import get_user_site
from ..api_services.pages_api import edit_page, get_page_text
from ..su_services.users_service import current_user
from .fixref_shared.fixred_worker import RunState, work_on_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: Literal["notext", "no_changes", "changes", "saved"]
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
    if user is None:
        return UpdaterOutcome(kind="notext")
    user_dict = {
        "access_token": user.access_token,
        "access_secret": user.access_secret,
    }
    site = get_user_site(user_dict)

    title = (title or "").strip()
    if not title:
        return UpdaterOutcome(kind="notext")

    old_text = get_page_text(title, site)
    if old_text is None:
        return UpdaterOutcome(kind="notext")

    if not old_text.strip():
        return UpdaterOutcome(kind="notext", old_text=old_text)

    state = RunState()
    try:
        new_text = work_on_text(title, old_text, site, state)
    except Exception:
        logger.exception("work_on_text failed for %s", title)
        raise

    if not new_text or not new_text.strip():
        return UpdaterOutcome(kind="notext", old_text=old_text)

    if new_text == old_text:
        return UpdaterOutcome(kind="no_changes", old_text=old_text, new_text=new_text)

    if save:
        result = edit_page(site, title, new_text, summary)
        if result.get("success"):
            return UpdaterOutcome(kind="saved", newrevid=result.get("newrevid", 0))

    return UpdaterOutcome(kind="changes", old_text=old_text, new_text=new_text)


__all__ = [
    "work_on_title",
]
