"""
add template:RTT {{RTT}} to all pages in Category:RTT
"""

from __future__ import annotations

import logging

import wikitextparser as wtp

from ....api_services import MwClientPage, get_template_pages
from ....api_services.category import get_category_members

logger = logging.getLogger(__name__)


def add_rtt_to_text(text: str, title: str) -> str:
    new_line = "{{RTT}}"

    if text.find(new_line) != -1:
        logger.info(f"page already tagged.{new_line}")
        return text

    target_templates = ["rtt"]

    parsed = wtp.parse(text)

    for temp in parsed.templates:

        name = str(temp.normal_name()).strip().lower().replace("_", " ")
        if name in target_templates:
            logger.info(f"page already tagged.{title=}")
            return text

    newtext = text

    last_section = None

    for section in parsed.sections:
        last_section = section

    category_found = False
    if last_section:
        for line in last_section.contents.split("\n"):
            if line.strip().lower().startswith("[[category:"):
                newtext = newtext.replace(line, f"{new_line}\n{line}", 1)
                category_found = True
                break
    if not category_found:
        newtext = f"{newtext.rstrip()}\n{new_line}"

    return newtext


def work_page(title):
    site = None

    page = MwClientPage(title, site)

    if not page.exists():
        return False

    ns = page.namespace

    if ns != 0:
        return False

    text = page.get_text()
    summary = ""

    newtext = add_rtt_to_text(text, title)

    if newtext != text:
        summary = "Added {{RTT}}"

        save = page.edit(
            text=newtext,
            summary=summary,
            nocreate=1,
        )

        return save

    return False


def run() -> None:
    site = None
    mdwiki_pages = get_category_members(
        site=site,
        category_title="Category:RTT",
        namespace=0,
    )

    template_pages = get_template_pages(
        "Template:RTT",
        namespace=0,
        site=site,
    )

    logger.info(f"len of mdwiki_pages: {len(mdwiki_pages)}, template_pages: {len(template_pages)}")
    pages_to_add = [x for x in mdwiki_pages if x not in template_pages]
    logger.info(f"len of pages_to_add: {len(pages_to_add)}")

    for x in pages_to_add:
        work_page(x)
