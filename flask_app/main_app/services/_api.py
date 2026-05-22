"""Shared MediaWiki API client used by service modules.

Keeps credential loading in one place so per-tool services don't each grow
their own copy of `_load_api()`.
"""

from __future__ import annotations

import functools
import os

from ..newapi import AllAPIS


@functools.lru_cache(maxsize=8)
def get_api(*, lang: str = "www", family: str = "mdwiki") -> AllAPIS:
    """Return a credentialed `AllAPIS` client, cached per (lang, family)."""

    username = os.getenv("WIKIPEDIA_HIMO_USERNAME")
    password = os.getenv("MDWIKI_HIMO_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "Missing credentials: set WIKIPEDIA_HIMO_USERNAME and MDWIKI_HIMO_PASSWORD"
        )
    return AllAPIS(
        lang=lang,
        family=family,
        username=username,
        password=password,
        use_cookies=False,
    )


__all__ = ["get_api"]
