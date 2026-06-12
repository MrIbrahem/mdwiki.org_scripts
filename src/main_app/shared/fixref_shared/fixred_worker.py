"""
Service: fix redirects in page text on mdwiki.
"""

from __future__ import annotations

import logging

import wikitextparser as wtp
from mwclient.client import Site

from ...api_services.query_api import get_page_links, resolve_redirects
from ..replace_wikilink import replace_wikilink_redirects
from .objects import RunState

logger = logging.getLogger(__name__)


def _replace_links(
    text: str,
    oldlink: str,
    newlink: str,
) -> str:
    """
    Mirror of legacy ``replace_links2``.

    Each wikilink
        - ``[[old]]`` becomes ``[[new|old]]`` (preserve the original display text);
        - ``[[old|...]]`` becomes ``[[new|...]]``.
    """
    parsed = wtp.parse(text)
    for wl in parsed.wikilinks:
        if wl.title == oldlink:
            if wl.text is None:
                wl.text = wl.target
            wl.title = newlink
    return str(parsed)


def replace_in_text(text: str, new_targets: dict[str, str]) -> str:
    newtext = text

    for oldlink, target in new_targets.items():
        newtext = replace_wikilink_redirects(newtext, oldlink, target)

    return newtext


def work_on_text(title: str, text: str, site: Site, state: RunState) -> str:
    """Fix redirect links in *text* for the given *title*."""

    links = get_page_links(title, site)

    for nor in links.get("normalized", []) or []:
        state.normalized[nor["to"]] = nor["from"]

    link_titles = list(links["links"].keys())
    if not link_titles:
        return text

    data = resolve_redirects(titles=link_titles, site=site)

    new_targets: dict[str, str] = {}
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
