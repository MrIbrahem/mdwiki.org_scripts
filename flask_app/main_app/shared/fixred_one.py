"""
Service: fix redirects in page text on mdwiki.
"""

from __future__ import annotations

import logging

from ..api_services.clients.wiki_client import get_user_site
from ..api_services.pages_api import edit_page, get_page_text
from ..su_services.users_service import current_user
from .fixref_shared.fixred_worker import work_on_text
from .fixref_shared.objects import RunState
from .shared_classes import UpdaterTextOutcome

logger = logging.getLogger(__name__)


def work_on_title(
    title: str,
    save: bool = False,
    summary: str = "Fix redirects.",
) -> UpdaterTextOutcome:
    """
    s
    """

    user = current_user()
    if user is None:
        return UpdaterTextOutcome(kind="skipped", msg="No user")

    user_dict = {
        "access_token": user.access_token,
        "access_secret": user.access_secret,
    }
    site = get_user_site(user_dict)

    title = (title or "").strip()
    if not title:
        return UpdaterTextOutcome(kind="skipped", msg="Invalid title")

    old_text = get_page_text(title, site)

    if not old_text or not old_text.strip():
        return UpdaterTextOutcome(kind="notext", old_text=old_text)

    state = RunState()
    try:
        new_text = work_on_text(title, old_text, site, state)
    except Exception:
        logger.exception("work_on_text failed for %s", title)
        raise

    if not new_text or not new_text.strip():
        return UpdaterTextOutcome(kind="notext", old_text=old_text)

    if new_text == old_text:
        return UpdaterTextOutcome(kind="skipped", msg="No changes")

    if save:
        result = edit_page(site, title, new_text, summary)
        if result.get("success"):
            return UpdaterTextOutcome(kind="saved", newrevid=result.get("newrevid", 0))

    return UpdaterTextOutcome(kind="changes", old_text=old_text, new_text=new_text)


__all__ = [
    "work_on_title",
]
