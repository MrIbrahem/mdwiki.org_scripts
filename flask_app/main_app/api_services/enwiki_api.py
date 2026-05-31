"""API client for English Wikipedia queries."""

from __future__ import annotations

import functools
import logging
import os

import requests

logger = logging.getLogger(__name__)

_USER_AGENT = os.getenv(
    "REDIRECT_USER_AGENT",
    "WikiProjectMed Translation Dashboard/1.0 (https://mdwiki.toolforge.org/; tools.mdwiki@toolforge.org)",
)


@functools.lru_cache(maxsize=1)
def _enwiki_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    return session


def get_redirects_for(title: str, *, timeout: int = 10) -> list[str]:
    """Fetch mainspace redirect titles pointing to *title* on enwiki.

    Args:
        title: The page title to look up redirects for.
        timeout: Request timeout in seconds.

    Returns:
        List of redirect titles (namespace 0 only).
    """
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
        for r in page.get("redirects", []) or []:
            # if page.get("title") != title: continue
            if r.get("ns") != 0:
                continue
            redirect_title = r.get("title", "")
            if redirect_title and redirect_title not in out:
                out.append(redirect_title)
    return out


__all__ = [
    "get_redirects_for",
]
