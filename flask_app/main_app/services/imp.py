"""Service: import revision history from English Wikipedia to mdwiki.

In-process replacement for ``python/imp.py``. For each input title:

1. Open the destination page on mdwiki.
2. Call ``page.import_page(family="wikipedia")`` to copy the full revision
   history via the MediaWiki ``action=import`` API.
3. If the import added any revisions, re-save the original mdwiki body on
   top (with ``nocreate=1``) so the visible content is unchanged.
4. If that save fails, fall back to writing the body to
   ``User:Mr._Ibrahem/<title>`` so the operator can recover it manually.
"""

from __future__ import annotations

import logging
from threading import Event
from typing import Any, Callable, Iterable, Optional

from ._api import get_api

logger = logging.getLogger(__name__)


def _process_one(api, title: str, *, save: bool, log: Callable[[str], None]) -> str:
    """Return one of: ``missing``, ``no-revisions``, ``imported``, ``imported-fallback``, ``error``."""

    page = api.MainPage(title)
    if not page.exists():
        log(f"{title!r}: missing on mdwiki")
        return "missing"

    text = page.get_text()
    if not save:
        log(f"{title!r}: would import (dry run)")
        return "imported"

    try:
        result = page.import_page(family="wikipedia") or {}
    except Exception as exc:  # noqa: BLE001
        logger.exception("import_page failed for %s", title)
        log(f"{title!r}: import error {exc!r}")
        return "error"

    revisions = (result.get("import") or [{}])[0].get("revisions", 0)
    if not revisions:
        log(f"{title!r}: import returned 0 revisions")
        return "no-revisions"

    log(f"{title!r}: imported {revisions} revision(s)")

    # Re-save the original body so the page content matches what the operator
    # saw before the import.
    saved = page.save(newtext=text, summary="", nocreate=1)
    if saved is True:
        return "imported"

    fallback_title = f"User:Mr._Ibrahem/{title}"
    log(f"{title!r}: top-level save failed ({saved!r}); writing to {fallback_title!r}")
    fallback_page = api.MainPage(fallback_title)
    fallback_save = fallback_page.save(
        newtext=text,
        summary="Returns the article text after importing the history",
        nocreate=0,
    )
    if fallback_save is True:
        return "imported-fallback"
    log(f"  fallback save failed too ({fallback_save!r})")
    return "error"


def run(
    *,
    titles: Iterable[str],
    from_lang: str = "en",  # reserved; current import_page only accepts family
    save: bool = True,
    on_progress: Optional[Callable[..., None]] = None,
    stop_event: Optional[Event] = None,
) -> dict[str, Any]:
    """Import revision history for each title.

    The ``from_lang`` parameter is reserved for future use; the underlying
    ``import_page`` API call currently only accepts a wiki family
    (``wikipedia``) and resolves the source language interwiki-style.
    """

    titles_list = [t.replace("_", " ").strip() for t in titles if t and t.strip()]

    def _emit(done: int, total: int, msg: str) -> None:
        if on_progress is not None:
            on_progress(done, total, message=msg)

    api = get_api()
    counts = {
        "scanned": 0,
        "imported": 0,
        "imported_fallback": 0,
        "no_revisions": 0,
        "missing": 0,
        "errors": 0,
        "total": len(titles_list),
        "from_lang": from_lang,
    }
    _emit(0, len(titles_list), f"importing history for {len(titles_list)} title(s)")

    for i, title in enumerate(titles_list, start=1):
        if stop_event is not None and stop_event.is_set():
            _emit(i - 1, len(titles_list), "stopped by user")
            break
        counts["scanned"] += 1

        try:
            outcome = _process_one(
                api,
                title,
                save=save,
                log=lambda m, _i=i, _n=len(titles_list): _emit(_i, _n, m),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("imp run failed for %s", title)
            counts["errors"] += 1
            _emit(i, len(titles_list), f"[{i}/{len(titles_list)}] {title}: error {exc!r}")
            continue

        _emit(i, len(titles_list), f"[{i}/{len(titles_list)}] {title}: {outcome}")
        if outcome == "imported":
            counts["imported"] += 1
        elif outcome == "imported-fallback":
            counts["imported_fallback"] += 1
        elif outcome == "no-revisions":
            counts["no_revisions"] += 1
        elif outcome == "missing":
            counts["missing"] += 1
        elif outcome == "error":
            counts["errors"] += 1

    return counts


__all__ = ["run"]
