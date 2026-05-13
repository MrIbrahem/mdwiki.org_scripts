#!/usr/bin/python3
"""

Category:CS1 errors: redundant parameter

python3 core8/pwb.py md_core/mdpy/fix_duplicate ask

"""
import functools
import os
import logging
import sys
from newapi import AllAPIS

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
    username = os.getenv("WIKIPEDIA_HIMO_USERNAME")
    password = os.getenv("MDWIKI_HIMO_PASSWORD")

    if not username or not password:
        raise RuntimeError("Missing credentials: WIKIPEDIA_HIMO_USERNAME / MDWIKI_HIMO_PASSWORD")

    return AllAPIS(
        lang="www",
        family="mdwiki",
        username=username,
        password=password,
        use_cookies=False,
    )


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


def fix_dup(from_title, to_title):
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
    fop = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "generator": "querypage",
        "redirects": 1,
        "utf8": 1,
        "gqppage": "DoubleRedirects",
        "gqplimit": "max",
    }
    # ---
    lista = post_s(fop)
    # ---
    redirects = lista.get("query", {}).get("redirects", [])
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
            fix_dup(from_title, to_title)


if __name__ == "__main__":
    main()
