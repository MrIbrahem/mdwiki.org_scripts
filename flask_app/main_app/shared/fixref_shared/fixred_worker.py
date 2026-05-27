"""
Service: fix redirects in page text on mdwiki.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Literal

import mwclient

from ...api_services.query_api import get_page_links, resolve_redirects

logger = logging.getLogger(__name__)

OutcomeKind = Literal["notext", "no_changes", "changes", "saved"]


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


def _replace_links(
    text: str,
    oldlink: str,
    oldlink2: str,
    newlink: str,
) -> str:
    """Mirror of legacy ``replace_links2``.

    Each wikilink ``[[old]]`` becomes ``[[new|old]]`` (preserve the original
    display text); ``[[old|...]]`` becomes ``[[new|...]]``. Also handles the
    normalized-title alias if present in ``state.normalized``.
    """

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


def replace_in_text(text, new_targets):
    newtext = text

    for oldlink2, target in new_targets.items():
        newtext = _replace_links(newtext, oldlink2, oldlink2, target)

    return newtext


def work_on_text(title: str, text: str, site: mwclient.Site, state: RunState) -> str:
    """Fix redirect links in *text* for the given *title*."""

    links = get_page_links(title, site)

    for nor in links.get("normalized", []) or []:
        state.normalized[nor["to"]] = nor["from"]

    link_titles = list(links["links"].keys())
    if not link_titles:
        return text

    data = resolve_redirects(titles=link_titles, site=site)

    new_targets = {}
    for _, info in links["links"].items():
        oldlink = info["title"]
        oldlink2 = data.get("normalized", {}).get(oldlink, oldlink)
        target = data.get("from_to", {}).get(oldlink) or data.get("from_to", {}).get(oldlink2)
        if target:
            new_targets[oldlink2] = target
            new_targets[oldlink] = target

    newtext = replace_in_text(text, new_targets)

    return newtext


__all__ = [
    "work_on_text",
    "RunState",
]
