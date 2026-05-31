""" """

from __future__ import annotations

import logging

import wikitextparser as wtp

logger = logging.getLogger(__name__)


def _normalize_mediawiki_title(title: str) -> str:
    """
    Normalizes a MediaWiki page title for accurate comparison.
    Handles spaces, underscores, and first-letter capitalization.
    """
    if not title:
        return title

    # Strip whitespaces and treat underscores as spaces
    title = title.strip().replace("_", " ")

    # Capitalize only the first character (MediaWiki standard)
    if title:
        title = title[0].upper() + title[1:]

    return title


def _replace_wikilink_destinations(text: str, redirect_to: str, final_target: str, set_text: bool = False) -> str:
    """
    Parses wikitext to find links pointing to a specific redirect
    and updates their title to point to the final target.
    Relies on wikitextparser native properties to preserve fragments and display text.

    Default:
        - ``[[old]]`` becomes ``[[new]]``.
        - ``[[old|...]]`` becomes ``[[new|...]]``.

    With `set_text=True`:
        - ``[[old]]`` becomes ``[[new|old]]`` (preserve the original display text)
    """
    parsed_text = wtp.parse(text)

    # Normalize the target we are searching for
    normalized_redirect = _normalize_mediawiki_title(redirect_to)

    for link in parsed_text.wikilinks:
        # Use native 'title' property instead of manually splitting the target
        if link.title is None:
            continue

        normalized_title = _normalize_mediawiki_title(link.title)

        # Compare the normalized titles
        if normalized_title == normalized_redirect:
            # Updating link.title automatically preserves link.fragment and link.text
            old_target = link.target
            old_title = link.title
            link.title = final_target

            if set_text and not link.text:
                # preserve the original display text
                link.text = old_target

            logger.debug(f"Replaced link title '{old_title}' with '{final_target}'")
    # Return the updated wikitext as a string
    return parsed_text.string


def replace_wikilink_destinations(text: str, redirect_to: str, final_target: str) -> str:
    """
    Parses wikitext to find links pointing to a specific redirect
    and updates their title to point to the final target.
    Relies on wikitextparser native properties to preserve fragments and display text.
    """
    return _replace_wikilink_destinations(text, redirect_to, final_target)


def replace_wikilink_redirects(text: str, redirect_to: str, final_target: str) -> str:
    """ """
    return _replace_wikilink_destinations(text, redirect_to, final_target, set_text=True)


__all__ = [
    "replace_wikilink_destinations",
    "replace_wikilink_redirects",
]
