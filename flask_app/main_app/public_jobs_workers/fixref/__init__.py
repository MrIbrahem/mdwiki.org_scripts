"""Service: normalize references on mdwiki pages.

In-process replacement for ``python/fixref/start.py``. Inputs are one of:

* ``titles``   — explicit list of page titles to process.
* ``category`` — name of a Category: page; we walk it via AllAPIS.CatDepth.
* ``number``   — when neither of the above is given, take the first N
                 mainspace pages (capped by :data:`MAX_PAGES_FIXREF`).

For every selected page we read the text, run the legacy
``fix_ref_template`` rewriter, and save the result if it changed.

The text-rewriter itself lives in ``python/fixref/fixref_text_new.py``; we
import it via the :mod:`._legacy` path-shim because re-implementing it is
out of scope for the migration (see ``docs/merge-plan.md`` §6).
"""

from __future__ import annotations

import logging
from threading import Event
from typing import Any, Callable, Iterable, Optional

from .._api import get_api
from .fixref_text_new import fix_ref_template

logger = logging.getLogger(__name__)

#: Hard ceiling on iteration size (mirrors legacy ``thenumbers[1]``).
MAX_PAGES_FIXREF = 20000


def _legacy_fix_ref_template(text: str) -> tuple[str, str]:
    """Run the legacy reference rewriter on a text block.

    Returns ``(new_text, summary)``. Imported lazily so the wikitextparser
    cost is paid only when the tool is actually used.
    """

    new_text, summary = fix_ref_template(text, returnsummary=True)
    return new_text, summary


def _resolve_targets(
    api,
    *,
    titles: Optional[Iterable[str]],
    category: Optional[str],
    number: Optional[int],
) -> list[str]:
    """Resolve which pages to process given the input options."""

    if titles:
        cleaned: list[str] = []
        seen: set[str] = set()
        for t in titles:
            if not t:
                continue
            t = t.replace("_", " ").strip()
            if not t or t in seen:
                continue
            seen.add(t)
            cleaned.append(t)
        return cleaned[:MAX_PAGES_FIXREF]

    if category:
        cat = category.strip()
        if not cat.lower().startswith("category:"):
            cat = f"Category:{cat}"
        members = api.CatDepth(cat, sitecode="www", family="mdwiki", depth=0, ns="0") or []
        # CatDepth may return either a list of titles or a dict keyed by title.
        if isinstance(members, dict):
            members = list(members.keys())
        return list(members)[:MAX_PAGES_FIXREF]

    if number:
        capped = min(int(number), MAX_PAGES_FIXREF)
        return api.NewApi().Get_All_pages("", limit_all=capped)[:capped]

    return []


def run(
    *,
    titles: Optional[Iterable[str]] = None,
    category: Optional[str] = None,
    number: Optional[int] = None,
    save: bool = True,
    on_progress: Optional[Callable[..., None]] = None,
    stop_event: Optional[Event] = None,
) -> dict[str, Any]:
    """Iterate the resolved targets and normalize references on each."""

    if not (titles or category or number):
        raise ValueError("fixref.run requires at least one of: titles, category, number")

    def _emit(done: int, total: int, msg: str) -> None:
        if on_progress is not None:
            on_progress(done, total, message=msg)

    api = get_api()
    pages = _resolve_targets(api, titles=titles, category=category, number=number)

    counts = {
        "scanned": 0,
        "fixed": 0,
        "no_changes": 0,
        "missing": 0,
        "errors": 0,
        "total": len(pages),
    }
    _emit(0, len(pages), f"processing {len(pages)} page(s)")

    for i, title in enumerate(pages, start=1):
        if stop_event is not None and stop_event.is_set():
            _emit(i - 1, len(pages), "stopped by user")
            break
        counts["scanned"] += 1

        try:
            page = api.MainPage(title)
            if not page.exists():
                counts["missing"] += 1
                _emit(i, len(pages), f"[{i}/{len(pages)}] {title}: missing")
                continue

            text = page.get_text() or ""
            new_text, summary = _legacy_fix_ref_template(text)
            if not summary:
                summary = "Normalize references"

            if new_text == text:
                counts["no_changes"] += 1
                _emit(i, len(pages), f"[{i}/{len(pages)}] {title}: no changes")
                continue

            if save:
                ok = page.save(newtext=new_text, summary=summary)
                if ok is True:
                    counts["fixed"] += 1
                    _emit(i, len(pages), f"[{i}/{len(pages)}] {title}: fixed")
                else:
                    counts["errors"] += 1
                    _emit(i, len(pages), f"[{i}/{len(pages)}] {title}: save failed ({ok!r})")
            else:
                counts["fixed"] += 1
                _emit(i, len(pages), f"[{i}/{len(pages)}] {title}: would-fix (dry run)")
        except Exception as exc:
            logger.exception("fixref failed for %s", title)
            counts["errors"] += 1
            _emit(i, len(pages), f"[{i}/{len(pages)}] {title}: error {exc!r}")

    return counts


__all__ = ["run", "MAX_PAGES_FIXREF"]
