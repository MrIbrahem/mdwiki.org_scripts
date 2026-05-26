""" """

from __future__ import annotations

import logging

import mwclient

from ..utils.verify import verify_required_fields
from .mwclient_page import MwClientPage

logger = logging.getLogger(__name__)


def is_page_exists(page_title: str, site: mwclient.Site) -> bool:
    return MwClientPage(page_title, site).check_exists()


def is_redirect(page_title: str, site: mwclient.Site) -> bool:
    return MwClientPage(page_title, site).is_redirect()


def edit_page(site: mwclient.Site, title: str, text: str, summary: str) -> dict[str, any]:
    return MwClientPage(title, site).edit_page(text, summary)


def move_page(
    site: mwclient.Site | None,
    title: str,
    new_title: str,
    reason: str = "",
    move_talk: bool = True,
    no_redirect: bool = False,
) -> dict[str, any]:
    """
    Move (rename) a page on Wikimedia Commons.

    Args:
        site: Authenticated mwclient.Site object for Commons.
        title: Current page title (e.g. "Template:OWID/foo").
        new_title: Target page title (e.g. "Template:OWID/Foo").
        reason: Move reason / log summary on the wiki.
        move_talk: Also move the associated talk page.
        no_redirect: Do not leave a redirect at the old title (requires
            the ``suppressredirect`` user right).

    Returns:
        A dictionary with ``success`` (bool) and ``error``/``details`` on failure,
        matching the shape returned by :func:`create_page` / :func:`edit_page`.
    """
    missing_fields = verify_required_fields({"title": title, "new_title": new_title, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for move_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return MwClientPage(title, site).move_page(
        new_title,
        reason=reason,
        move_talk=move_talk,
        no_redirect=no_redirect,
    )


def create_page(
    page_name: str,
    wikitext: str,
    site: mwclient.Site | None,
    summary: str = "",
) -> dict:
    """
    Create a new page on Wikimedia Commons.

    Args:
        page_name: The name of the page to create.
        wikitext: The wikitext content for the new page.
        site: Authenticated mwclient.Site object for Commons.
        summary: Edit summary.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str) on failure.
    """
    missing_fields = verify_required_fields({"page_name": page_name, "wikitext": wikitext, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for create_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return edit_page(site, page_name, wikitext, summary)


def update_page_text(
    page_name: str,
    updated_text: str,
    site: mwclient.Site | None,
    summary: str = "",
) -> dict:
    """
    Update the wikitext of any page on Wikimedia Commons.

    Args:
        page_name: The name of the page to update.
        updated_text: The new wikitext content.
        site: Authenticated mwclient.Site object for Commons.
        summary: Edit summary.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str) on failure.
    """
    missing_fields = verify_required_fields({"page_name": page_name, "updated_text": updated_text, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_page_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return edit_page(site, page_name, updated_text, summary)


def is_pages_exists(
    titles: list[str],
    site: mwclient.Site,
) -> dict[str, bool]:
    result = {}

    for i in range(0, len(titles), 50):
        group = titles[i : i + 50]
        json1 = site.get("query", titles="|".join(group))

        query = json1.get("query", {})

        normalized = {red["to"]: red["from"] for red in query.get("normalized", [])}

        query_pages = query.get("pages", {})
        for _, kk in query_pages.items():
            title = kk.get("title", "")
            if title:
                original_title = normalized.get(title, title)
                result[original_title] = "missing" not in kk

    return result


def resolve_redirects(
    titles: list[str],
    site: mwclient.Site,
) -> dict[str, bool]:
    normalized = {}
    from_to = {}

    for i in range(0, len(titles), 50):
        group = titles[i : i + 50]
        params = {
            "prop": "redirects",
            "redirects": 1,
            "converttitles": 1,
            "utf8": 1,
            "rdlimit": "max",
        }
        data = site.get("query", titles="|".join(group), **params)
        query = data.get("query", {}) or {}

        for nor in query.get("normalized", []) or []:
            normalized[nor["to"]] = nor["from"]

        # Top-level redirects array: page is a redirect TO some target.
        for red in query.get("redirects", []) or []:
            from_to[red["from"]] = red["to"]

        # Per-page redirects array: pages that redirect TO this title.
        for page in (query.get("pages", {}) or {}).values():
            target = page.get("title", "")
            for src in page.get("redirects", []) or []:
                from_to[src["title"]] = target

    result = {
        "normalized": normalized,
        "from_to": from_to,
    }

    return result


def get_page_text(page_title: str, site: mwclient.Site) -> str | None:
    """Return the wikitext of *page_title*, or None if the page is missing."""
    page = site.pages[page_title]
    if not page.exists:
        return None
    return page.text()


def search_pages(
    query: str,
    site: mwclient.Site,
    namespace: int = 0,
    limit: int = "max",
) -> list[str]:
    """Return page titles matching *query* via the MediaWiki search API."""
    titles: list[str] = []
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": str(namespace),
        "srlimit": str(limit),
        "srwhat": "text",
        "srsort": "just_match",
    }
    data = site.get("query", **params)
    for item in (data.get("query", {}).get("search", []) or []):
        titles.append(item["title"])
    return titles


def get_double_redirects(site: mwclient.Site) -> list[dict[str, str]]:
    """Return resolved double-redirect pairs ``[{"from", "to"}, ...]``."""
    params = {
        "action": "query",
        "prop": "info",
        "generator": "querypage",
        "redirects": 1,
        "utf8": 1,
        "gqppage": "DoubleRedirects",
        "gqplimit": "max",
    }
    data = site.get("query", **params)
    return data.get("query", {}).get("redirects", []) or []


def import_page_from_wiki(
    site: mwclient.Site,
    title: str,
    family: str = "wikipedia",
) -> dict:
    """Import revision history of *title* from another wiki family.

    Uses the MediaWiki ``action=import`` API (interwiki import).
    Returns the API response dict.
    """
    params = {
        "action": "import",
        "title": title,
        "interwikisource": family,
        "fullhistory": 1,
    }
    try:
        result = site.post(**params)
        return result or {}
    except Exception as exc:
        logger.exception("import_page_from_wiki failed for %s", title)
        return {"error": str(exc)}


def get_page_links(
    title: str,
    site: mwclient.Site,
    namespace: int = 0,
) -> dict:
    """Return wikilinks on *title* in *namespace*.

    Returns ``{"links": {title: {"ns", "title"}}, "normalized": [...], "redirects": [...]}``.
    """
    params = {
        "action": "query",
        "prop": "links",
        "titles": title,
        "plnamespace": str(namespace),
        "pllimit": "max",
        "converttitles": 1,
    }
    data = site.get("query", **params)
    out: dict = {"links": {}, "normalized": [], "redirects": []}
    if not data:
        return out

    query = data.get("query", {}) or {}
    out["normalized"] = query.get("normalized", []) or []
    out["redirects"] = query.get("redirects", []) or []
    for page in (query.get("pages", {}) or {}).values():
        for link in page.get("links", []) or []:
            out["links"][link["title"]] = {"ns": link["ns"], "title": link["title"]}
    return out


__all__ = [
    "create_page",
    "get_double_redirects",
    "get_page_links",
    "get_page_text",
    "import_page_from_wiki",
    "is_page_exists",
    "is_pages_exists",
    "is_redirect",
    "move_page",
    "resolve_redirects",
    "search_pages",
    "update_page_text",
]
