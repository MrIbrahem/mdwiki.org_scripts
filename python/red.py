#!/usr/bin/python3
"""

نسخ التحويلات من الإنجليزية إلى mdwiki

"""

import functools
import logging
import sys

import requests
from python.mdwiki_page import MainPage, NewApi

logger = logging.getLogger(__name__)

user_agent = "mdwiki.org tools/1.0 (https://mdwiki.toolforge.org/; tools.mdwiki@toolforge.org)"

# ---
offset = {1: 0}
# ---
to_make = {}
# ---
for arg in sys.argv:
    arg, _, value = arg.partition(":")
    # ---
    if arg.lower() in ["offset", "-offset"] and value.isdigit():
        offset[1] = int(value)

falses = [
    "category:",
    "file:",
    "template:",
    "user:",
    # "video:",
    "wikipedia:",
]


def valid_title(title: str) -> bool:
    # ---
    title = title.lower().strip()
    # ---
    if title.find("(disambiguation)") != -1:
        return False
    # ---
    # if title.startswith('category:') or title.startswith('file:') or title.startswith('template:') or title.startswith('user:'):
    return not any(title.startswith(prefix) for prefix in falses)


@functools.lru_cache(maxsize=1)
def _load_session() -> requests.Session:
    Session = requests.Session()
    Session.headers.update({"User-Agent": user_agent})
    return Session


def get_red(title):
    # ---
    params = {
        "action": "query",
        "format": "json",
        "prop": "redirects",
        "titles": title,
        "utf8": 1,
        "rdprop": "title",
        "rdlimit": "max",
    }
    # ---
    lista = []
    # ---
    Session = _load_session()
    # ---
    r22 = Session.post(
        "https://en.wikipedia.org/w/api.php",
        data=params,
        timeout=10,
    )
    json1 = r22.json()
    # ---
    pages = json1.get("query", {}).get("pages", {})
    # ---szs
    for x in pages:
        title = pages[x].get("title", "")
        redirectsn = pages[x].get("redirects", [])
        logger.info(redirectsn)
        if pages[x]["title"] == title:
            for io in redirectsn:
                if io["ns"] != 0:
                    continue
                # ---
                if io["title"] not in lista:
                    lista.append(io["title"])
    # ---
    return lista


def work(title, num, length, From=""):
    # ---
    logger.info(f'-------------------------------------------\n*<<yellow>> >{num}/{length} title:"{title}".')
    # ---
    api_new = NewApi("www", family="mdwiki")
    # ---
    if num < offset[1]:
        return ""
    # ---
    page = MainPage(title, "www", family="mdwiki")
    exists = page.exists()
    if not exists:
        logger.info(f" page:{title} not exists in mdwiki.")
        return ""
    # ---
    redirects = get_red(title)
    # ---
    logger.info(redirects)
    # ---
    text = f"#redirect [[{title}]]"
    sus = f"Redirected page to [[{title}]]"
    # ---
    ing = api_new.Find_pages_exists_or_not(redirects)
    # ---
    num = 0
    # ---
    for tit, o in ing.items():
        num += 1
        if o:
            logger.info(f"page n:{num}, title:'{tit}' already in mdwiki.org..")
            continue
        # ---
        if not valid_title(tit):
            continue
        # ---
        new_page = MainPage(tit, "www", family="mdwiki")
        exists = new_page.exists()
        if not exists:
            new_page.create(text, sus)


def main():
    logger.info("*<<red>> > :")
    # ---
    api_new = NewApi("www", family="mdwiki")
    # ---
    # python3 red.py -page:Allopurinol
    # python3 red.py -page:Activated_charcoal_\(medication\)
    # python3 red.py -newpages:10
    # python red.py -newpages:1000
    # python red.py -newpages:20000
    # ---
    page2 = ""
    From = "0"
    # ---
    for arg in sys.argv:
        arg, _, value = arg.partition(":")
        # ---
        arg = arg.lower()
        # ---
        if arg == "-from":
            From = value
        # ---
        if arg in ["-page2", "page2"]:
            page2 = value
    # ---
    if page2 != "" and From != "":
        work(page2, 0, 1, From=From)
    # ---
    user = ""
    user_limit = "3000"
    # ---
    searchlist = {
        "drug": "insource:/https\\:\\/\\/druginfo\\.nlm\\.nih\\.gov\\/drugportal\\/name\\/lactulose/",
    }
    # ---
    limite = "max"
    starts = ""
    # ---
    pages = []
    # ---
    namespaces = "0"
    newpages = ""
    # ---
    for arg in sys.argv:
        arg, _, value = arg.partition(":")
        # ---
        arg = arg.lower()
        # ---
        if arg in ["-limit", "limit"]:
            limite = value
        # ---
        if arg in ["-userlimit", "userlimit"]:
            user_limit = value
        # ---
        if arg in ["-page", "page"]:
            pages.append(value)
        # ---
        if arg in ["-page2", "page2"]:
            value = value
            pages.append(value)
        # ---
        if arg in ["newpages", "-newpages"]:
            newpages = value
        # ---
        # python red.py -ns:0 -usercontribs:Edoderoobot
        # python red.py -ns:0 -usercontribs:Ghuron
        if arg in ["-user", "-usercontribs"]:
            user = value
        # ---
        # python red.py -start:!
        if arg in ["start", "-start"]:
            starts = value
        # ---
        if arg == "-ns":
            namespaces = value
        # ---
        # python red.py -file:mdwiki/list.txt
        # python3 red.py -file:mdwiki/list.txt
        if arg == "-file":
            # ---
            # if value == 'redirectlist.txt' :
            # ---
            with open(value, "r", encoding="utf8") as text2:
                text = text2.read()

            pages.extend(x.strip() for x in text.split("\n"))
        # ---
        # python red.py -ns:0 search:drug
        if arg == "search":
            if value in searchlist:
                value = searchlist[value]
            # ---
            ccc = api_new.Search(value=value, ns="0", srlimit="max")
            for x in ccc:
                pages.append(x)
            # ---
    # ---
    start_done = starts
    okay = True
    # ---
    if starts == "all":
        while okay:
            # ---
            if starts == start_done:
                okay = False
            # ---
            # python red.py -start:all
            #
            # ---
            list = api_new.Get_All_pages(start="", namespace=namespaces, limit=limite)
            start_done = starts
            for num, page in enumerate(list, start=1):
                work(page, num, len(list))
                # ---
                starts = page
    # ---
    if starts != "":
        listen = api_new.Get_All_pages(start=starts, namespace=namespaces, limit=limite)
        for num, page in enumerate(listen, start=1):
            work(page, num, len(listen))
            # ---
    # ---
    list = []
    # ---
    if newpages != "":
        list = api_new.Get_Newpages(limit=newpages, namespace=namespaces)
    elif user != "":
        list = api_new.UserContribs(user, limit=user_limit, namespace=namespaces, ucshow="new")
    elif pages != []:
        list = pages
    for num, page in enumerate(list, start=1):
        work(page, num, len(list))
    # ---
    # '''
    # ---
    if starts == "all":
        while okay:
            # ---
            if starts == start_done:
                okay = False
            # ---
            # python red.py -start:all
            #
            # ---
            list = api_new.Get_All_pages(start="", namespace=namespaces, limit=limite)
            start_done = starts
            for num, page in enumerate(list, start=1):
                work(page, num, len(list))
                # ---
                starts = page
    elif starts != "":
        # while start_done != starts :
        while okay:
            # ---
            if starts == start_done:
                okay = False
            # ---
            # python red.py -start:! -limit:3
            #
            # ---
            list = api_new.Get_All_pages(start=starts, namespace=namespaces, limit=limite)
            start_done = starts
            for num, page in enumerate(list, start=1):
                work(page, num, len(list))
                # ---
                starts = page


if __name__ == "__main__":
    main()
