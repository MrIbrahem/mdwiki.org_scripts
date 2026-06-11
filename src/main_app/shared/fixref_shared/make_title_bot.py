#!/usr/bin/python3
"""
# ---
from md_core.mdpy.bots import make_title_bot
# _title1_ = make_title_bot.make_title(url)
# ---
"""

import logging
import re
from typing import Dict
from urllib.parse import quote

from ...api_services.citation_api import get_citation_title

logger = logging.getLogger(__name__)

# ---
globalbadtitles = r"""
# is
(test|
# starts with
    ^\W*(
            register
            |registration
            |(sign|log)[ \-]?in
            |subscribe
            |sign[ \-]?up
            |log[ \-]?on
            |untitled[ ]?(document|page|\d+|$)
            |404[ ]
        ).*
# anywhere
    |.*(
            403[ ]forbidden
            |(404|page|file|information|resource).*not([ ]*be)?[ ]*(available|found)
            |site.*disabled
            |error[ ]404
            |error.+not[ ]found
            |not[ ]found.+error
            |404[ ]error
            |\D404\D
            |check[ ]browser[ ]settings
            |log[ \-]?(on|in)[ ]to
            |site[ ]redirection
     ).*
# ends with
    |.*(
            register
            |access denied
            |registration
            |(sign|log)[ \-]?in
            |subscribe|sign[ \-]?up
            |log[ \-]?on
        )\W*$
)
"""


def make_title(url: str, cache: Dict[str, str] | None = None) -> str:
    if cache is None:
        cache = {}
    url = url.strip()
    if not url:
        logger.info("<<red>> url = '' return False")
        return ""

    if url in cache:
        return cache[url]

    cache[url] = ""

    url2 = quote(url)
    url2 = url2.replace("/", "%2F")
    url2 = url2.replace(":", "%3A")
    url2 = url2.replace("&", "%26")
    url2 = url2.replace("#", "%23")

    title = get_citation_title(url2)

    if not title or title.strip().lower() == "not found.":
        return ""

    titleBlackList = re.compile(globalbadtitles, re.I | re.S | re.X)
    if titleBlackList.match(title):
        logger.error(f"<<red>> WARNING<<default>> {url} : Blacklisted title ({title})")

    cache[url] = title

    if title:
        logger.info(f"<<green>> make_title_bot: newtitle: ({title})")

    return title


__all__ = [
    "make_title",
]
