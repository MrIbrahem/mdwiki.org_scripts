#!/usr/bin/python3
"""

إيجاد التحويلات واصلاحها

python3 core8/pwb.py md_core/mdpy/fixred

"""
import functools
import logging
import re
import sys

from python.mdwiki_page import NewApi, md_MainPage

from .mdapi import post_s

logger = logging.getLogger(__name__)

from_to = {}
normalized = {}


@functools.lru_cache(maxsize=1)
def load_nonredirects() -> list[str]:
    api_new = NewApi("www", family="mdwiki")
    nonredirects = api_new.Get_All_pages("!", namespace="0", apfilterredir="nonredirects")
    logger.info(f"len of nonredirects {len(nonredirects)} ")
    return nonredirects


def find_redirects(links):
    # ---
    # titles = [ x for x in links if links[x].get('ns','') == '0' ]
    titles = []
    for x in links:
        if x not in from_to:
            ns = links[x].get("ns", "")
            if str(ns) == "0":
                titles.append(x)
            else:
                logger.info(f"ns:{str(ns)}")
    # ---
    oldlen = len(from_to.items())
    # ---
    normalized_numb = 0
    # ---
    for i in range(0, len(titles), 300):
        group = titles[i : i + 300]
        # ---
        # logger.info(group)
        # ---
        line = "|".join(group)
        # ---
        params = {
            "action": "query",
            "format": "json",
            "prop": "redirects",
            "titles": line,
            "redirects": 1,
            "converttitles": 1,
            "utf8": 1,
            "rdlimit": "max",
        }
        if jsone := post_s(params):
            # ---
            query = jsone.get("query", {})
            # ---
            # "normalized": [{"from": "tetracyclines","to": "Tetracyclines"}]
            normal = query.get("normalized", [])
            for nor in normal:
                normalized[nor["to"]] = nor["from"]
                normalized_numb += 1
                # logger.info('normalized["%s"] = "%s"' % ( nor["to"] , nor["from"] ) )
            # ---
            # "redirects": [{"from": "Acetylsalicylic acid","to": "Aspirin"}]
            Redirects = query.get("redirects", [])
            for red in Redirects:
                from_to[red["from"]] = red["to"]
                # logger.info('from_to["%s"] = "%s"' % ( red["from"] , red["to"] ) )
            # ---
            # "pages": { "4195": {"pageid": 4195,"ns": 0,"title": "Aspirin","redirects": [{"pageid": 4953,"ns": 0,"title": "Acetylsalicylic acid"}]} }
            pages = query.get("pages", {})
            # ---
            for page in pages:
                # tab = {"pageid": 4195,"ns": 0,"title": "Aspirin","redirects": [{"pageid": 4953,"ns": 0,"title": "Acetylsalicylic acid"}]}
                tab = pages[page]
                for pa in tab.get("redirects", []):
                    from_to[pa["title"]] = tab["title"]
                    # logger.info('<<yellow>> from_to["%s"] = "%s"' % ( pa["title"] , tab["title"] ) )
        else:
            logger.info(" no jsone")
    # ---
    newlen = len(from_to.items())
    nn = newlen - oldlen
    # ---
    logger.info(f"def : find {nn} length")
    # logger.info( "def find_redirects: find %d for normalized" % normalized_numb )


def replace_links2(text, oldlink, newlink):
    # ---
    oldlink2 = normalized.get(oldlink, oldlink)
    # ---
    while (
        text.find(f"[[{oldlink}]]") != -1
        or text.find(f"[[{oldlink}|") != -1
        or text.find(f"[[{oldlink2}]]") != -1
        or text.find(f"[[{oldlink2}|") != -1
    ):
        # ---
        logger.info(f"text.replace( '[[{oldlink}]]' , '[[{newlink}|{oldlink}]]' )")
        # ---
        text = text.replace(f"[[{oldlink}]]", f"[[{newlink}|{oldlink}]]")
        text = text.replace(f"[[{oldlink}|", f"[[{newlink}|")
        # ---
        text = re.sub(r"\[\[%s(\|\]\])" % oldlink, r"[[%s\g<1>" % newlink, text, flags=re.IGNORECASE)
        # ---
        if oldlink != oldlink2:
            text = re.sub(r"\[\[%s(\|\]\])" % oldlink2, r"[[%s\g<1>" % newlink, text, flags=re.IGNORECASE)
            text = text.replace(f"[[{oldlink2}]]", f"[[{newlink}|{oldlink2}]]")
            text = text.replace(f"[[{oldlink2}|", f"[[{newlink}|")
    # ---
    return text


def Get_page_links(title, namespace="0", limit="max"):
    # ---
    logger.info(f' for title:"{title}", limit:"{limit}",namespace:"{namespace}"')
    # ---
    params = {
        "action": "query",
        "prop": "links",
        "titles": title,
        "plnamespace": namespace,
        "pllimit": limit,
        "converttitles": 1,
    }
    # ---
    json1 = post_s(params) or {}
    # ---
    Main_table = {
        "links": {},
        "normalized": [],
        "redirects": [],
    }
    # ---
    if json1:
        # ---
        query = json1.get("query", {})
        Main_table["normalized"] = query.get("normalized", [])
        Main_table["redirects"] = query.get("redirects", [])
        # ---
        pages = query.get("pages", {})
        # ---
        for page in pages:
            tab = pages[page]
            for pa in tab.get("links", []):
                Main_table["links"][pa["title"]] = {"ns": pa["ns"], "title": pa["title"]}
    else:
        logger.info("mdwiki_api.py no json1")
    # ---
    logger.info(f"mdwiki_api.py : find {len(Main_table['links'])} pages.")
    # ---
    return Main_table


def treat_page(title):
    """
    Change all redirects from the current page to actual links.
    """
    # ---
    page = md_MainPage(title, "www", family="mdwiki")
    _exists = page.exists()
    # ---
    text = page.get_text()
    # ---
    # links = page.page_links_query(plnamespace="0")
    links = Get_page_links(title, namespace="0", limit="max")
    # ---
    normal = links.get("normalized", [])
    logger.info(f"find {len(normal)} normalized..")
    # ---
    for nor in normal:
        normalized[nor["to"]] = nor["from"]
        logger.info(f"normalized[\"{nor['to']}\"] = \"{nor['from']}\"")
    # ---
    newtext = text
    # ---
    find_redirects(links["links"])
    # ---
    nonredirects = load_nonredirects()
    # ---
    for tt in links["links"]:
        # ---
        page = links["links"][tt]
        tit = page["title"]
        tit2 = normalized.get(page["title"], page["title"])
        # ---
        if fixed_tit := from_to.get(tit) or from_to.get(tit2):
            newtext = replace_links2(newtext, tit, fixed_tit)
        elif tit not in nonredirects:
            if tit2 != tit:
                logger.info(f'<<red>> tit:["{tit}"] and tit:["{tit2}"] not in from_to')
    # ---
    _save_page = page.save(newtext=newtext, summary="Fix redirects")


def main():
    # ---
    ttab = []
    # ---
    # python3 fixred.py
    # python  fixred.py -page:WikiProjectMed:List ask
    # python  fixred.py -page:User:Mr._Ibrahem/sandbox
    # python3 fixred.py -page:Tetracycline_antibiotics
    # ---
    for arg in sys.argv:
        arg, _, value = arg.partition(":")
        # ---
        if arg in ["-page2", "page2"]:
            value = value.strip()
            ttab.append(value.strip())
        # ---
        if arg == "-page":
            ttab.append(value)
    # ---
    if ttab in [[], ["all"]]:
        nonredirects = load_nonredirects()
        ttab = nonredirects
    # ---
    for title in ttab:
        treat_page(title)


if __name__ == "__main__":
    main()
