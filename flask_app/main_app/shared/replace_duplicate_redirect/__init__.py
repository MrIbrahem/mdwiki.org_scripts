""" """

from __future__ import annotations

import wikitextparser as wtp
import logging

logger = logging.getLogger(__name__)


def replace_redirect_link(text: str, redirect_to: str, final_target: str) -> str:
    # TODO: replace only the link not the whole text, use wikitextparser to analyze the text, then search in text for links to redirect_to then replace it to final_target
    new_text = f"#REDIRECT [[{final_target}]]"
    return new_text


def replace_wikilink_destinations(text: str, redirect_to: str, final_target: str) -> str:
    """
    Parses wikitext to find links pointing to a specific redirect
    and updates them to point to the final target.
    """
    # Parse the wikitext into a WikitextParser object
    parsed_text = wtp.parse(text)

    # Iterate through all wikilinks found in the text
    for link in parsed_text.wikilinks:
        # Check if the link's target matches the one we want to replace.
        # strip() is used to safely handle any unexpected whitespace.
        if link.target.strip() == redirect_to.strip():
            # Update the target to the new destination
            link.target = final_target
            logger.debug(f"Replaced link target '{redirect_to}' with '{final_target}'")

    # Return the updated wikitext as a string
    return parsed_text.string
