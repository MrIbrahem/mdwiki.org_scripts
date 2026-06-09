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

from ..api_services import MwClientPage
from ..api_services.clients.wiki_client import get_user_site
from ..su_services.current_user import CurrentUser
from .new_updater import med_updater_one
from .shared_classes import UpdaterTextOutcome

logger = logging.getLogger(__name__)


def newupdater_one_title(
    title: str,
    save: bool = False,
    summary: str = "Med updater.",
    user: CurrentUser | None = None,
) -> UpdaterTextOutcome:
    """
    Fetch the page, run the updater, and report what the diff would be.
    """
    title = (title or "").strip()
    if not title:
        return UpdaterTextOutcome(kind="skipped", msg="Invalid title")

    if user is None:
        return UpdaterTextOutcome(kind="skipped", msg="No user")

    site = get_user_site(user.to_auth_payload())

    page = MwClientPage(title, site)
    old_text = page.get_text()

    if not old_text or not old_text.strip():
        return UpdaterTextOutcome(kind="notext", old_text=old_text)

    try:
        new_text = med_updater_one(title, old_text)
    except Exception:
        logger.exception("work_on_text failed for %s", title)
        raise

    if not new_text or not new_text.strip():
        return UpdaterTextOutcome(kind="notext", old_text=old_text)

    if new_text == old_text:
        return UpdaterTextOutcome(kind="skipped", msg="No changes")

    if save:
        result = page.edit(new_text, summary)
        if result.get("success"):
            return UpdaterTextOutcome(kind="saved", newrevid=result.get("newrevid", 0))

    return UpdaterTextOutcome(kind="changes", old_text=old_text, new_text=new_text)


__all__ = [
    "newupdater_one_title",
]
