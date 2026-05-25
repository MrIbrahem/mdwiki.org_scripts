"""Service: find-and-replace bot for mdwiki.

In-process replacement for ``python/find_replace_bot/one_job.py``. The legacy
implementation kept job state in files on disk (``find.txt``, ``replace.txt``,
``stop.txt``, ``log.txt``, ``done.txt``); the merge plan replaces all of that
with the in-process job runner.

Algorithm per page:

* Read the page text.
* Compute ``new_text = text.replace(find, replace)``.
* If unchanged → log no-op, continue.
* Else save with the documented edit summary.

Stop semantics: the ``stop_event`` parameter is checked between pages, so a
user-clicked stop takes effect at the next page boundary (cooperative).
"""

from __future__ import annotations

import logging
from threading import Event
from typing import Any, Callable, Literal, Optional

from ._api import get_api

logger = logging.getLogger(__name__)

ListType = Literal["newlist", "oldlist"]


def _resolve_titles(api, *, find: str, listtype: ListType) -> list[str]:
    """Pick the page list to walk based on ``listtype``."""

    if listtype == "newlist":
        # Use search so we only visit pages that actually contain `find`.
        return (
            api.NewApi().Search(
                value=find,
                ns="0",
                srlimit="max",
                return_dict=False,
                addparams={"srsort": "just_match", "srwhat": "text"},
            )
            or []
        )
    # oldlist: walk every mainspace page.
    return api.NewApi().Get_All_pages() or []


def _process_one(
    api,
    title: str,
    *,
    find: str,
    replace: str,
    save: bool,
    log: Callable[[str], None],
) -> str:
    """Return one of: ``missing``, ``no-changes``, ``changed``, ``error``."""

    page = api.MainPage(title)
    if not page.exists():
        return "missing"

    text = page.get_text() or ""
    if not text.strip():
        return "no-changes"

    new_text = text.replace(find, replace)
    if new_text == text:
        return "no-changes"
    if not save:
        log(f"  would change (dry run)")
        return "changed"

    summary = f"Replace via mdwiki.toolforge.org find-and-replace tool."
    saved = page.save(newtext=new_text, summary=summary)
    if saved is True:
        return "changed"
    log(f"  save failed: {saved!r}")
    return "error"


def run(
    *,
    find: str,
    replace: str = "",
    listtype: ListType = "newlist",
    number: Optional[int] = None,
    save: bool = True,
    on_progress: Optional[Callable[..., None]] = None,
    stop_event: Optional[Event] = None,
) -> dict[str, Any]:
    """Iterate the resolved page list and apply ``find -> replace`` per page.

    ``number`` caps the count of *successful modifications* (matching the
    legacy semantics), not the iteration size. Pass ``None`` for unlimited.
    """

    if not find:
        raise ValueError("replace.run requires a non-empty `find`")
    if listtype not in ("newlist", "oldlist"):
        raise ValueError(f"invalid listtype: {listtype!r}")

    def _emit(done: int, total: int, msg: str) -> None:
        if on_progress is not None:
            on_progress(done, total, message=msg)

    api = get_api()
    titles = _resolve_titles(api, find=find, listtype=listtype)
    cap = int(number) if number and number > 0 else None

    counts = {
        "scanned": 0,
        "changed": 0,
        "no_changes": 0,
        "missing": 0,
        "errors": 0,
        "total": len(titles),
        "stopped": False,
        "cap": cap,
    }
    _emit(0, len(titles), f"start work in {len(titles)} pages")

    for i, title in enumerate(titles, start=1):
        if stop_event is not None and stop_event.is_set():
            counts["stopped"] = True
            _emit(i - 1, len(titles), "stopped by user")
            break
        if cap is not None and counts["changed"] >= cap:
            _emit(i - 1, len(titles), f"reached cap of {cap} modifications")
            break

        counts["scanned"] += 1

        try:
            outcome = _process_one(
                api,
                title,
                find=find,
                replace=replace,
                save=save,
                log=lambda m, _i=i, _n=len(titles): _emit(_i, _n, m),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("replace failed for %s", title)
            counts["errors"] += 1
            _emit(i, len(titles), f"[{i}/{len(titles)}] {title}: error {exc!r}")
            continue

        _emit(i, len(titles), f"[{i}/{len(titles)}] {title}: {outcome}")
        if outcome == "changed":
            counts["changed"] += 1
        elif outcome == "no-changes":
            counts["no_changes"] += 1
        elif outcome == "missing":
            counts["missing"] += 1
        elif outcome == "error":
            counts["errors"] += 1

    return counts


__all__ = ["run", "ListType"]
