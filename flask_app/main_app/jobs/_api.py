"""Shared MediaWiki API client used by service modules.

Keeps credential loading in one place so per-tool services don't each grow
their own copy of `_load_api()`.
"""

from __future__ import annotations

import functools
import os

from ..newapi import AllAPIS


@functools.lru_cache(maxsize=8)
def get_api(*, lang: str = "", family: str = "") -> AllAPIS:
    """Return a credentialed `AllAPIS` client, cached per (lang, family)."""

    lang = lang or os.getenv("WIKI_LANG") or "www"
    family = family or os.getenv("WIKI_FAMILY") or "mdwiki"
    username = os.getenv("WIKI_USERNAME")
    password = os.getenv("WIKI_PASSWORD")

    if not username or not password:
        raise RuntimeError("Missing credentials: set WIKI_USERNAME and WIKI_PASSWORD")

    return AllAPIS(
        lang=lang,
        family=family,
        username=username,
        password=password,
        use_cookies=False,
    )


__all__ = ["get_api"]
