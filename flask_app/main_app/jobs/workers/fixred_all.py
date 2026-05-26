"""Service: fix redirects in page text on mdwiki.

In-process replacement for ``python/fixred_all.py``. For one or more pages we:

1. Read the page text.
2. Enumerate the wikilinks the page contains (``prop=links``).
3. For each chunk of those targets, ask the API which are redirects
   (``prop=redirects``) and resolve each to its canonical target.
4. Rewrite the page so every redirect link points to the canonical target,
   preserving the original display text via piped wikilinks.
5. Save the result with a "Fix redirects" edit summary.

The legacy script kept ``from_to`` and ``normalized`` as module globals; here
they live in :class:`RunState` so concurrent jobs can't collide.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from threading import Event
from typing import Any, Callable, Optional

import mwclient

from ...api_services.clients.wiki_client import get_user_site
from ...newapi import AllAPIS
from ...su_services.users_service import current_user
from .._api import get_api

from ...shared.fixref_shared.fixred_worker import work_on_text

logger = logging.getLogger(__name__)

_NS_MAIN = "0"


@dataclass
class RunState:
    """Per-run mutable state.

    ``from_to``    maps redirect source -> resolved target.
    ``normalized`` maps the API-normalized title -> the input title (for
                   case-corrected matching when the page text uses a different
                   capitalization than the canonical title).
    """

    from_to: dict[str, str] = field(default_factory=dict)
    normalized: dict[str, str] = field(default_factory=dict)


def _treat_page(api: AllAPIS, title: str, state: RunState, *, save: bool, site: mwclient.Site) -> tuple[str, str]:
    """Return one of: ``missing``, ``no-changes``, ``would-fix``, ``fixed``, ``error``."""

    page = api.MainPage(title)
    if not page.exists():
        return "missing", ""

    text = page.get_text()

    newtext = work_on_text(api, title, text, site=site, state=state)

    if newtext == text:
        return "no-changes", text

    if not save:
        return "would-fix", newtext

    ok = page.save(newtext=newtext, summary="Fix redirects")
    if ok is True:
        return "fixed", newtext

    return "error", text


def run_all(
    save: bool = True,
    on_progress: Optional[Callable[..., None]] = None,
    stop_event: Optional[Event] = None,
) -> dict[str, Any]:
    """ """

    user = current_user()
    site = get_user_site(user)

    def _emit(done: int, total: int, msg: str) -> None:
        if on_progress is not None:
            on_progress(done, total, message=msg)

    api = get_api()
    state = RunState()

    # titles = api.NewApi().Get_All_pages( start="!", namespace=_NS_MAIN, apfilterredir="nonredirects")
    titles = site.allpages(
        start="!",
        prefix=None,
        namespace=_NS_MAIN,
        filterredir="all",
        minsize=None,
        maxsize=None,
        prtype=None,
        prlevel=None,
        limit=None,
        dir="ascending",
        filterlanglinks="all",
        generator=True,
        end=None,
        max_items=None,
        api_chunk_size=None,
    )

    counts = {
        "scanned": 0,
        "fixed": 0,
        "no_changes": 0,
        "missing": 0,
        "errors": 0,
        "total": len(titles),
    }
    _emit(0, len(titles), f"processing {len(titles)} title(s)")

    for i, t in enumerate(titles, start=1):
        if stop_event is not None and stop_event.is_set():
            _emit(i - 1, len(titles), "stopped by user")
            break
        counts["scanned"] += 1
        try:
            outcome, _ = _treat_page(api, t, state, save=save, site=site)
        except Exception as exc:
            logger.exception("treat_page failed for %s", t)
            counts["errors"] += 1
            _emit(i, len(titles), f"[{i}/{len(titles)}] {t}: error {exc!r}")
            continue

        if outcome == "fixed":
            counts["fixed"] += 1
        elif outcome == "no-changes":
            counts["no_changes"] += 1
        elif outcome == "missing":
            counts["missing"] += 1
        elif outcome == "would-fix":
            counts["fixed"] += 1  # treat dry-run successes as fixes for reporting
        elif outcome == "error":
            counts["errors"] += 1

        _emit(i, len(titles), f"[{i}/{len(titles)}] {t}: {outcome}")

    return counts


def fix_text(text):
    return text


__all__ = [
    "run_all",
    "fix_text",
]
