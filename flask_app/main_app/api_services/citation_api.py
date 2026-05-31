"""API client for Wikipedia citation/REST endpoints."""

from __future__ import annotations

import logging

import requests

from ..config import settings

logger = logging.getLogger(__name__)

_CITATION_BASE = "https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki-basefields"


def get_citation_title(url_encoded_fields: str, *, timeout: int = 10) -> str:
    """Fetch a citation title from Wikipedia's citation REST API.

    Args:
        url_encoded_fields: URL-encoded citation fields (already percent-encoded).
        timeout: Request timeout in seconds.

    Returns:
        The citation title string, or empty string on failure.
    """
    url = f"{_CITATION_BASE}/{url_encoded_fields}"
    try:
        req = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": settings.other.user_agent},
        )

        if 500 <= req.status_code < 600:
            logger.info(f"received {req.status_code} status from {req.url}")

        req.raise_for_status()
        json1 = req.json()

    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout Error for URL [{url}]: {e}")
        return ""
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error for URL [{url}]: {e}")
        return ""
    except ValueError as e:
        logger.error(f"JSON Decode Error for URL [{url}]: {e}")
        return ""
    except requests.exceptions.RequestException as e:
        logger.error(f"Network Request Error for URL [{url}]: {e}")
        return ""
    except Exception:
        logger.exception("Unexpected Exception occurred:")
        return ""

    if not json1:
        return ""

    results = json1[0] if isinstance(json1, list) else json1
    return results.get("title", "")


__all__ = [
    "get_citation_title",
]
