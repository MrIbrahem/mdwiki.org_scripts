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

from ._api import get_api
from . import _legacy

logger = logging.getLogger(__name__)

OutcomeKind = Literal["notext", "no_changes", "changes"]


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: OutcomeKind
    old_text: str = ""
    new_text: str = ""

    @property
    def has_changes(self) -> bool:
        return self.kind == "changes"


def _legacy_work_on_text(title: str, text: str) -> str:
    """Call the legacy text-rewriting orchestrator.

    Imported lazily so the heavy ``wikitextparser`` import only happens when
    the tool is actually used, and so a missing legacy directory doesn't
    break Flask boot.
    """

    _legacy.install()
    from new_updater import work_on_text  # type: ignore[import-not-found]

    return work_on_text(title, text)


def work_on_title(title: str) -> UpdaterOutcome:
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
        new_text = _legacy_work_on_text(title, old_text)
    except Exception:  # noqa: BLE001 - the legacy code can raise widely
        logger.exception("work_on_text failed for %s", title)
        raise

    if not new_text or not new_text.strip():
        return UpdaterOutcome(kind="notext", old_text=old_text)
    if new_text == old_text:
        return UpdaterOutcome(kind="no_changes", old_text=old_text, new_text=new_text)
    return UpdaterOutcome(kind="changes", old_text=old_text, new_text=new_text)


def save_page(title: str, *, summary: str = "Med updater.") -> tuple[bool, str]:
    """Re-run :func:`work_on_title` and save the result if it changed.

    We deliberately re-run the rewrite server-side instead of accepting a
    posted ``new_text`` so a malicious form submission can't trick us into
    saving arbitrary content. The trade-off is that the saved content
    reflects the page as-of the save click, not the preview.

    Returns ``(saved_ok, status_label)`` where ``status_label`` is one of
    ``saved``, ``no_changes``, ``notext``, ``save_failed``.
    """

    outcome = work_on_title(title)
    if outcome.kind == "notext":
        return False, "notext"
    if outcome.kind == "no_changes":
        return False, "no_changes"

    api = get_api()
    page = api.MainPage(title)
    ok = page.save(newtext=outcome.new_text, summary=summary)
    if ok is True:
        return True, "saved"
    logger.warning("save_page %s failed: %r", title, ok)
    return False, "save_failed"


__all__ = ["UpdaterOutcome", "work_on_title", "save_page"]
