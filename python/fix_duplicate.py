#!/usr/bin/python3
"""

Category:CS1 errors: redundant parameter

python3 core8/pwb.py md_core/mdpy/fix_duplicate ask

"""
import functools
import logging
import os
import sys

from flask_app.main_app.api_services.newapi import AllAPIS

logger = logging.getLogger(__name__)

# ---
offset = {1: 0}
# ---
for arg in sys.argv:
    arg, _, value = arg.partition(":")
    # ---
    if arg.lower() in ["offset", "-offset"] and value.isdigit():
        offset[1] = int(value)
# ---
from_to = {}


@functools.lru_cache(maxsize=1)
def load_main_api() -> AllAPIS:
    username = os.getenv("WIKI_USERNAME")
    password = os.getenv("WIKI_PASSWORD")

    if not username or not password:
        raise RuntimeError("Missing credentials: WIKI_USERNAME / WIKI_PASSWORD")

    return AllAPIS(
        lang="www",
        family="mdwiki",
        username=username,
        password=password,
        use_cookies=False,
    )


def _list_double_redirects(api: AllAPIS) -> list[dict[str, str]]:
    """Return the resolved ``[{"from", "to"}, ...]`` redirect list."""

    new_api = api.NewApi()
    params = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "generator": "querypage",
        "redirects": 1,
        "utf8": 1,
        "gqppage": "DoubleRedirects",
        "gqplimit": "max",
    }
    data = new_api.post_params(params, method="post") or {}
    return data.get("query", {}).get("redirects", []) or []


def post_s(params, addtoken=False, files=None):
    # ---
    main_api = load_main_api()
    # ---
    api_new = main_api.NewApi("www", family="mdwiki")
    # ---
    params["format"] = "json"
    params["utf8"] = 1
    # ---
    json1 = api_new.post_params(params, addtoken=addtoken, files=files)
    # ---
    return json1


def _fix_one(from_title, to_title):
    """Treat one double redirect."""
    # ---
    if to_title in from_to:
        to_title = from_to[to_title]
    # ---
    newtext = f"#REDIRECT [[{to_title}]]"
    # ---
    main_api = load_main_api()
    # ---
    page = main_api.MainPage(from_title, "www", family="mdwiki")
    _exists = page.exists()
    # ---
    oldtext = page.get_text()
    # ---
    sus = f"fix duplicate redirect to [[{to_title}]]"
    # ---
    if oldtext == newtext:
        logger.info("no changes.")
        return False
    # ---
    return page.save(newtext=newtext, summary=sus)


def main():
    logger.info("*<<red>> > :")
    # ---
    # python3 dup.py -page:Allopurinol
    # python3 dup.py -page:Activated_charcoal_\(medication\)
    # python3 dup.py -newpages:10
    # python dup.py -newpages:1000
    # python dup.py -newpages:20000
    # ---
    api = load_main_api()
    # ---
    redirects = _list_double_redirects(api)
    # ---
    for gg in redirects:
        from_title = gg["from"]
        to_title = gg["to"]
        from_to[from_title] = to_title
    # ---
    for nu, title in enumerate(redirects, start=1):
        from_title = title["from"]
        logger.info(f'-------\n*<<yellow>> >{nu}/{len(redirects)} from_title:"{from_title}".')
        to_title = title["to"]
        if to_title in from_to:
            _fix_one(from_title, to_title)


if __name__ == "__main__":
    main()
