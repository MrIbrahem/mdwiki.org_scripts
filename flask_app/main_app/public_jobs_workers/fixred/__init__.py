"""Service: fix redirects in page text on mdwiki.

In-process replacement for ``python/fixred.py``. For one or more pages we:

1. Read the page text.
2. Enumerate the wikilinks the page contains (``prop=links``).
3. For each chunk of those targets, ask the API which are redirects
   (``prop=redirects``) and resolve each to its canonical target.
4. Rewrite the page so every redirect link points to the canonical target,
   preserving the original display text via piped wikilinks.
5. Save the result with a "Fix redirects" edit summary.

The legacy script kept ``from_to`` and ``normalized`` as module globals; here
they live in :class:`_RunState` so concurrent jobs can't collide.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from threading import Event
from typing import Any, Callable, Literal, Optional

from ...api_services.newapi import AllAPIS
from .._api import get_api

logger = logging.getLogger(__name__)

_LINK_CHUNK = 300
_NS_MAIN = "0"


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


@dataclass
class _RunState:
    """Per-run mutable state.

    ``from_to``    maps redirect source -> resolved target.
    ``normalized`` maps the API-normalized title -> the input title (for
                   case-corrected matching when the page text uses a different
                   capitalization than the canonical title).
    """

    from_to: dict[str, str] = field(default_factory=dict)
    normalized: dict[str, str] = field(default_factory=dict)


def _post(api: AllAPIS, params: dict) -> dict:
    """Thin wrapper around the configured client. Returns ``{}`` on failure."""

    return api.NewApi().post_params(params, method="post") or {}


def _list_nonredirects(api: AllAPIS) -> list[str]:
    """All mainspace non-redirect titles. Cached on the API client by Get_All_pages."""

    return api.NewApi().Get_All_pages(
        start="!",
        namespace=_NS_MAIN,
        apfilterredir="nonredirects",
    )


def _get_page_links(api: AllAPIS, title: str) -> dict[str, Any]:
    """Mirror of legacy ``Get_page_links`` using the new API client."""

    params = {
        "action": "query",
        "prop": "links",
        "titles": title,
        "plnamespace": _NS_MAIN,
        "pllimit": "max",
        "converttitles": 1,
    }
    data = _post(api, params)
    out: dict[str, Any] = {"links": {}, "normalized": [], "redirects": []}
    if not data:
        return out

    query = data.get("query", {}) or {}
    out["normalized"] = query.get("normalized", []) or []
    out["redirects"] = query.get("redirects", []) or []
    for page in (query.get("pages", {}) or {}).values():
        for link in page.get("links", []) or []:
            out["links"][link["title"]] = {"ns": link["ns"], "title": link["title"]}
    return out


def _resolve_redirects_for(api: AllAPIS, state: _RunState, link_titles: list[str]) -> None:
    """Populate ``state.from_to`` / ``state.normalized`` for a batch of link titles."""

    # Skip titles already known to map.
    pending = [t for t in link_titles if t not in state.from_to]
    for i in range(0, len(pending), _LINK_CHUNK):
        chunk = pending[i : i + _LINK_CHUNK]
        params = {
            "action": "query",
            "format": "json",
            "prop": "redirects",
            "titles": "|".join(chunk),
            "redirects": 1,
            "converttitles": 1,
            "utf8": 1,
            "rdlimit": "max",
        }
        data = _post(api, params)
        if not data:
            continue
        query = data.get("query", {}) or {}

        for nor in query.get("normalized", []) or []:
            state.normalized[nor["to"]] = nor["from"]

        # Top-level redirects array: page is a redirect TO some target.
        for red in query.get("redirects", []) or []:
            state.from_to[red["from"]] = red["to"]

        # Per-page redirects array: pages that redirect TO this title.
        for page in (query.get("pages", {}) or {}).values():
            target = page.get("title", "")
            for src in page.get("redirects", []) or []:
                state.from_to[src["title"]] = target


def _replace_links(text: str, oldlink: str, oldlink2: str, newlink: str) -> str:
    """Mirror of legacy ``replace_links2``.

    Each wikilink ``[[old]]`` becomes ``[[new|old]]`` (preserve the original
    display text); ``[[old|...]]`` becomes ``[[new|...]]``. Also handles the
    normalized-title alias if present in ``state.normalized``.
    """

    while f"[[{oldlink}]]" in text or f"[[{oldlink}|" in text or f"[[{oldlink2}]]" in text or f"[[{oldlink2}|" in text:
        text = text.replace(f"[[{oldlink}]]", f"[[{newlink}|{oldlink}]]")
        text = text.replace(f"[[{oldlink}|", f"[[{newlink}|")

        text = re.sub(
            rf"\[\[{re.escape(oldlink)}(\|\]\])",
            rf"[[{newlink}\g<1>",
            text,
            flags=re.IGNORECASE,
        )

        if oldlink != oldlink2:
            text = re.sub(
                rf"\[\[{re.escape(oldlink2)}(\|\]\])",
                rf"[[{newlink}\g<1>",
                text,
                flags=re.IGNORECASE,
            )
            text = text.replace(f"[[{oldlink2}]]", f"[[{newlink}|{oldlink2}]]")
            text = text.replace(f"[[{oldlink2}|", f"[[{newlink}|")

    return text


def _treat_page(api: AllAPIS, title: str, state: _RunState, *, save: bool) -> tuple[str, str]:
    """Return one of: ``missing``, ``no-changes``, ``would-fix``, ``fixed``, ``error``."""

    page = api.MainPage(title)
    if not page.exists():
        return "missing", ""

    text = page.get_text()
    links = _get_page_links(api, title)

    for nor in links.get("normalized", []) or []:
        state.normalized[nor["to"]] = nor["from"]

    link_titles = list(links["links"].keys())
    if not link_titles:
        return "no-changes", text

    _resolve_redirects_for(api, state, link_titles)

    new_targets = {}
    for _, info in links["links"].items():
        oldlink = info["title"]
        oldlink2 = state.normalized.get(oldlink, oldlink)
        target = state.from_to.get(oldlink) or state.from_to.get(oldlink2)
        if target:
            new_targets[oldlink2] = target
            new_targets[oldlink] = target

    newtext = replace_in_text(text, new_targets)

    if newtext == text:
        return "no-changes", text

    if not save:
        return "would-fix", newtext

    ok = page.save(newtext=newtext, summary="Fix redirects")
    if ok is True:
        return "fixed", newtext

    return "error", text


def replace_in_text(text, new_targets):
    newtext = text

    for oldlink2, target in new_targets.items():
        newtext = _replace_links(newtext, oldlink2, oldlink2, target)

    return newtext


def _work_on_text(api, title, text) -> str:
    """ """
    state = _RunState()

    links = _get_page_links(api, title)

    for nor in links.get("normalized", []) or []:
        state.normalized[nor["to"]] = nor["from"]

    link_titles = list(links["links"].keys())
    if not link_titles:
        return text

    _resolve_redirects_for(api, state, link_titles)

    new_targets = {}
    for _, info in links["links"].items():
        oldlink = info["title"]
        oldlink2 = state.normalized.get(oldlink, oldlink)
        target = state.from_to.get(oldlink) or state.from_to.get(oldlink2)
        if target:
            new_targets[oldlink2] = target
            new_targets[oldlink] = target

    newtext = replace_in_text(text, new_targets)

    return newtext


def run_all(
    save: bool = True,
    on_progress: Optional[Callable[..., None]] = None,
    stop_event: Optional[Event] = None,
) -> dict[str, Any]:
    """ """

    def _emit(done: int, total: int, msg: str) -> None:
        if on_progress is not None:
            on_progress(done, total, message=msg)

    api = get_api()
    state = _RunState()

    titles = _list_nonredirects(api)

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
            outcome, _ = _treat_page(api, t, state, save=save)
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
        new_text = _work_on_text(api, title, old_text)
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


def fix_text(text):
    return text


__all__ = [
    "run_all",
    "work_on_title",
    "fix_text",
]
