""" """

from __future__ import annotations

import logging
from typing import Any

import mwclient

from .mwclient_page import MwClientPage

logger = logging.getLogger(__name__)


def is_page_exists(page_title: str, site: mwclient.Site) -> bool:
    return MwClientPage(page_title, site).exists()


def is_redirect(page_title: str, site: mwclient.Site) -> bool:
    return MwClientPage(page_title, site).is_redirect()

def edit_page(site: mwclient.Site, title: str, text: str, summary: str) -> dict[str, Any]:
    return MwClientPage(title, site).edit(text, summary)


def move_page(
    site: mwclient.Site | None,
    title: str,
    new_title: str,
    reason: str = "",
    move_talk: bool = True,
    no_redirect: bool = False,
) -> dict[str, Any]:
    return MwClientPage(title, site).move(
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
    return MwClientPage(page_name, site).create(wikitext, summary)


def update_page_text(
    page_name: str,
    updated_text: str,
    site: mwclient.Site | None,
    summary: str = "",
) -> dict:
    return MwClientPage(page_name, site).edit(updated_text, summary)


def get_page_text(
    page_title: str,
    site: mwclient.Site | None,
) -> str:
    return MwClientPage(page_title, site).get_text()


__all__ = [
    "create_page",
    "get_page_text",
    "is_page_exists",
    "is_redirect",
    "move_page",
    "update_page_text",
]
