"""Service: copy redirects from English Wikipedia to mdwiki.

In-process replacement for ``python/red.py``. For each input title:

1. Query enwiki for the list of pages that redirect TO that title.
2. Filter out namespaced and disambiguation titles via :func:`_valid_title`.
3. Check which of those titles already exist on mdwiki.
4. Create a ``#redirect [[<title>]]`` page on mdwiki for the missing ones.

The enwiki query uses an anonymous ``requests`` session with a polite
user-agent — no credentials required for read-only API use.
"""

from __future__ import annotations

import functools
import logging
import os
from threading import Event
from typing import Any, Callable, Iterable, Optional

import requests

from ._api import get_api

logger = logging.getLogger(__name__)

_USER_AGENT = os.getenv(
    "REDIRECT_USER_AGENT",
    "WikiProjectMed Translation Dashboard/1.0 (https://mdwiki.toolforge.org/; tools.mdwiki@toolforge.org)",
)

# Title prefixes we never copy as redirects (case-insensitive match).
_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "category:",
    "file:",
    "template:",
    "user:",
    "wikipedia:",
)


@functools.lru_cache(maxsize=1)
def _enwiki_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    return session


def _valid_title(title: str) -> bool:
    """True iff this title should be copied as a redirect on mdwiki."""

    lower = title.lower().strip()
    if "(disambiguation)" in lower:
        return False
    return not any(lower.startswith(p) for p in _FORBIDDEN_PREFIXES)


def _enwiki_redirects_for(title: str, *, timeout: int = 10) -> list[str]:
    """Mainspace redirect titles pointing to ``title`` on enwiki."""

    session = _enwiki_session()
    params = {
        "action": "query",
        "format": "json",
        "prop": "redirects",
        "titles": title,
        "utf8": 1,
        "rdprop": "title",
        "rdlimit": "max",
    }
    response = session.post("https://en.wikipedia.org/w/api.php", data=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json() or {}
    pages = (payload.get("query") or {}).get("pages") or {}

    out: list[str] = []
    for page in pages.values():
        # Only consider redirects to the canonical (matching) title.
        if page.get("title") != title:
            continue
        for r in page.get("redirects", []) or []:
            if r.get("ns") != 0:
                continue
            redirect_title = r.get("title", "")
            if redirect_title and redirect_title not in out:
                out.append(redirect_title)
    return out


def _process_one(api, title: str, *, save: bool, log: Callable[[str], None]) -> dict[str, int]:
    """Copy missing redirects for one source title; return per-title counts."""

    counts = {"target_missing": 0, "created": 0, "already_exists": 0, "skipped": 0, "errors": 0}

    target_page = api.MainPage(title)
    if not target_page.exists():
        log(f"target {title!r} missing on mdwiki, skipping")
        counts["target_missing"] = 1
        return counts

    redirect_titles = _enwiki_redirects_for(title)
    if not redirect_titles:
        log(f"{title!r}: no redirects on enwiki")
        return counts

    existing = api.NewApi().Find_pages_exists_or_not(redirect_titles, noprint=True) or {}

    redirect_text = f"#redirect [[{title}]]"
    summary = f"Redirected page to [[{title}]]"

    for r_title, r_exists in existing.items():
        if r_exists:
            counts["already_exists"] += 1
            continue
        if not _valid_title(r_title):
            counts["skipped"] += 1
            continue

        try:
            new_page = api.MainPage(r_title)
            if new_page.exists():
                counts["already_exists"] += 1
                continue
            if not save:
                counts["created"] += 1
                continue
            new_page.create(redirect_text, summary)
        except Exception as exc:  # noqa: BLE001
            logger.exception("create redirect failed: %s -> %s", r_title, title)
            counts["errors"] += 1
            log(f"  {r_title!r}: error {exc!r}")
            continue
        counts["created"] += 1
        log(f"  created {r_title!r} -> {title!r}")

    return counts


def run(
    *,
    titles: Iterable[str],
    save: bool = True,
    on_progress: Optional[Callable[..., None]] = None,
    stop_event: Optional[Event] = None,
) -> dict[str, Any]:
    """Iterate ``titles`` and copy enwiki redirects for each."""

    titles_list = [t.replace("_", " ").strip() for t in titles if t and t.strip()]

    def _emit(done: int, total: int, msg: str) -> None:
        if on_progress is not None:
            on_progress(done, total, message=msg)

    api = get_api()
    totals = {
        "scanned": 0,
        "target_missing": 0,
        "created": 0,
        "already_exists": 0,
        "skipped": 0,
        "errors": 0,
        "total": len(titles_list),
    }
    _emit(0, len(titles_list), f"processing {len(titles_list)} title(s)")

    for i, title in enumerate(titles_list, start=1):
        if stop_event is not None and stop_event.is_set():
            _emit(i - 1, len(titles_list), "stopped by user")
            break
        totals["scanned"] += 1
        _emit(i, len(titles_list), f"[{i}/{len(titles_list)}] {title}")

        try:
            counts = _process_one(
                api,
                title,
                save=save,
                log=lambda m, _i=i, _n=len(titles_list): _emit(_i, _n, m),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("redirect run failed for %s", title)
            totals["errors"] += 1
            _emit(i, len(titles_list), f"[{i}/{len(titles_list)}] {title}: error {exc!r}")
            continue

        for key, val in counts.items():
            totals[key] = totals.get(key, 0) + val

    return totals


__all__ = ["run"]
