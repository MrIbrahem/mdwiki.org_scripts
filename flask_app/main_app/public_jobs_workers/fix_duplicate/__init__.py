"""Service: fix duplicate redirects on mdwiki.

In-process replacement for ``python/fix_duplicate.py``. Same algorithm:

1. Query ``Special:DoubleRedirects`` via ``generator=querypage`` with
   ``redirects=1`` so the API resolves the chain into a flat ``redirects``
   list of ``{"from", "to"}`` pairs.
2. Build a ``from -> to`` map across the whole result.
3. Re-walk the list and, for any source whose target is itself a key in the
   map, rewrite the source page to point at the final target.

The service is reentrant: credentials and the API client are cached via
``functools.lru_cache`` but no module-level mutable state leaks across runs.
"""

from __future__ import annotations

import logging
from threading import Event
from typing import Any, Callable, Optional

from ...api_services.newapi import AllAPIS
from .._api import get_api

logger = logging.getLogger(__name__)


def _list_double_redirects(api: AllAPIS) -> list[dict[str, str]]:
    """Return the resolved ``[{"from", "to"}, ...]`` redirect list."""

    new_api = api.NewApi()
    params = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "generator": "querypage",
        "redirects": 1,
        "utf8": 1,
        "gqppage": "DoubleRedirects",
        "gqplimit": "max",
    }
    data = new_api.post_params(params, method="post") or {}
    return data.get("query", {}).get("redirects", []) or []


def _fix_one(api: AllAPIS, from_title: str, final_target: str, *, save: bool) -> str:
    """Treat one double redirect; return a short outcome label."""

    page = api.MainPage(from_title)
    if not page.exists():
        return "missing"

    oldtext = page.get_text()
    newtext = f"#REDIRECT [[{final_target}]]"

    if oldtext == newtext:
        return "unchanged"

    if not save:
        return "would-fix"

    summary = f"fix duplicate redirect to [[{final_target}]]"
    ok = page.save(newtext=newtext, summary=summary)
    return "fixed" if ok is True else f"error:{ok!r}"


def run(
    *,
    save: bool = True,
    offset: int = 0,
    on_progress: Optional[Callable[..., None]] = None,
    stop_event: Optional[Event] = None,
) -> dict[str, Any]:
    """Iterate ``DoubleRedirects`` and fix each entry.

    Returns a count summary suitable for display on the job page.
    """

    def _emit(done: int, total: int, msg: str) -> None:
        if on_progress is not None:
            on_progress(done, total, message=msg)

    api = get_api()
    redirects = _list_double_redirects(api)

    # Build the chain map first, exactly like the legacy script.
    from_to = {entry["from"]: entry["to"] for entry in redirects if "from" in entry and "to" in entry}

    # Apply the offset to the iteration but keep the map intact.
    work = redirects[offset:]
    total = len(work)
    counts = {
        "scanned": 0,
        "fixed": 0,
        "unchanged": 0,
        "missing": 0,
        "skipped": 0,
        "errors": 0,
        "total": total,
    }
    _emit(0, total, f"loaded {len(redirects)} redirects, processing {total} starting at offset {offset}")

    for i, entry in enumerate(work, start=1):
        if stop_event is not None and stop_event.is_set():
            _emit(i - 1, total, "stopped by user")
            break

        from_title = entry.get("from", "")
        intermediate = entry.get("to", "")
        # Only entries whose `to` is itself a redirect-source are *double*.
        final_target = from_to.get(intermediate, "")

        counts["scanned"] += 1

        if not from_title or not final_target:
            counts["skipped"] += 1
            _emit(i, total, f"[{i}/{total}] skip {from_title!r}: not a double redirect")
            continue

        try:
            outcome = _fix_one(api, from_title, final_target, save=save)
        except Exception as exc:
            logger.exception("failed for %s -> %s", from_title, final_target)
            counts["errors"] += 1
            _emit(i, total, f"[{i}/{total}] {from_title}: error {exc!r}")
            continue

        if outcome == "fixed":
            counts["fixed"] += 1
        elif outcome == "unchanged":
            counts["unchanged"] += 1
        elif outcome == "missing":
            counts["missing"] += 1
        elif outcome.startswith("error"):
            counts["errors"] += 1

        _emit(i, total, f"[{i}/{total}] {from_title} -> {final_target}: {outcome}")

    return counts


__all__ = ["run"]
