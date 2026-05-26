""" """

from __future__ import annotations

import logging

import mwclient

from ..utils.verify import verify_required_fields

logger = logging.getLogger(__name__)


def get_page_text(
    page_name: str,
    site: mwclient.Site | None,
) -> str:
    """
    Get the wikitext of any page on Wikimedia Commons.

    Args:
        page_name: The name of the page (e.g., "Template:OWID/Barley yields").
        site: Authenticated mwclient.Site object for Commons.

    Returns:
        The wikitext of the page, or an empty string if it cannot be retrieved.
    """
    missing_fields = verify_required_fields(
        {
            "page_name": page_name,
            "site": site,
        }
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for get_page_text: {list_str}")
        return ""

    try:
        page = site.pages[page_name]
        return page.text()
    except Exception as exc:
        logger.exception(f"Failed to retrieve wikitext for {page_name}", exc_info=exc)
        return ""


__all__ = [
    "get_page_text",
]
