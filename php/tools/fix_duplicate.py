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

my_username = os.getenv("WIKIPEDIA_HIMO_USERNAME")
mdwiki_pass = os.getenv("MDWIKI_HIMO_PASSWORD")


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


def page_put(
    newtext="",
    summary="",
    title="",
    minor="",
    nocreate=1,
    **kwargs,
):
    # ---
    main_api = load_main_api()
    # ---s
    page = main_api.MainPage(title, "www", family="mdwiki")
    _exists = page.exists()
    # ---
    save_page = page.save(newtext=newtext, summary=summary, nocreate=nocreate, minor=minor)
    # ---
    return save_page


def GetPageText(title, redirects=False, get_revid=False):
    """Retrieve the wikitext of a specified page from a wiki.

    This function sends a request to a wiki API to retrieve the wikitext of
    a page identified by its title. It can handle redirects and can
    optionally return the revision ID of the page. If the page does not
    exist or cannot be parsed, appropriate messages are logged.

    Args:
        title (str): The title of the page to retrieve.
        redirects (bool?): Whether to follow redirects. Defaults to False.
        get_revid (bool?): Whether to return the revision ID along with the wikitext.
            Defaults to False.

    Returns:
        str: The wikitext of the specified page.
        tuple: A tuple containing the wikitext and the revision ID if get_revid is
            True.
    """

    # logger.info( '**GetarPageText: ')
    # ---
    params = {
        "action": "parse",
        # "prop": "wikitext|sections",
        "prop": "wikitext|revid",
        "page": title,
        # "redirects": 1,
        # "normalize": 1,
    }
    # ---
    if redirects:
        params["redirects"] = 1
    # ---
    text = ""
    # ---
    json1 = post_s(params)
    if json1:
        text = json1.get("parse", {}).get("wikitext", {}).get("*", "")
    else:
        logger.info("no parse in json1:")
        logger.info(json1)
    # ---
    if not text:
        logger.info(f'page {title} text == "".')
    # ---
    if get_revid:
        return text, json1.get("parse", {}).get("revid", 0)
    # ---
    return text


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


def fix_dup(From, To):
    """Treat one double redirect."""
    # ---
    if To in from_to:
        To = from_to[To]
    # ---
    newtext = f"#REDIRECT [[{To}]]"
    # ---
    oldtext = GetPageText(From)
    # ---
    sus = f"fix duplicate redirect to [[{To}]]"
    # ---
    if oldtext == newtext:
        logger.info("no changes.")
        return
    # ---
    page_put(oldtext=oldtext, newtext=newtext, summary=sus, title=From, returntrue=False, diff=True)


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
        From = gg["from"]
        To = gg["to"]
        from_to[From] = To
    # ---
    for nu, title in enumerate(redirects, start=1):
        From = title["from"]
        logger.info(f'-------\n*<<yellow>> >{nu}/{len(redirects)} From:"{From}".')
        To = title["to"]
        if To in from_to:
            fix_dup(From, To)


if __name__ == "__main__":
    main()
