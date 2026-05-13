#!/usr/bin/python3
"""
python3 core8/pwb.py newupdater/medask -page:Haemophilus_influenzae
python3 core8/pwb.py newupdater/medask -page:Crohn's_disease
python3 core8/pwb.py newupdater/medask -newpages:1000
python3 core8/pwb.py newupdater/medask -newpages:20000
python3 core8/pwb.py newupdater/medask -ns:0 search:drug
python3 core8/pwb.py newupdater/medask -start:!
python3 core8/pwb.py newupdater/medask -ns:0 -usercontribs:Edoderoobot
python3 core8/pwb.py newupdater/medask -ns:0 -usercontribs:Ghuron
"""

import logging
import sys
import urllib
import urllib.parse
from pathlib import Path

if Dir := Path(__file__).parent.parent:
    sys.path.append(str(Dir))

import mdapi
from md_core_helps.apis import mdwiki_api_call
from mdwiki_api.mdwiki_page import NewApi
from new_updater import work_on_text

logger = logging.getLogger(__name__)

# ---
api_new = NewApi("www", family="mdwiki")


def get_new_text(title):
    # ---
    # if not text:
    text = mdapi.GetPageText(title)
    # ---
    newtext = text
    # ---
    if newtext != "":
        newtext = work_on_text(title, newtext)
    # ---
    return text, newtext


def work_on_title(title, returntext=False):
    # ---
    title = urllib.parse.unquote(title)
    # ---
    text, new_text = get_new_text(title)
    # ---
    if text == "" or new_text == "":
        logger.info("<<red>> notext")
        return
    # ---
    if text == new_text:
        logger.info("no changes")
        return
    # ---
    ask = input(f"<<yellow>> save title:{title}? ")
    # ---
    if ask in ["y", "", "a"]:
        return mdapi.page_put(new_text, "mdwiki changes.", title)
    # ---
    print("not saved")
    return


def main1():
    # ---
    if sys.argv and sys.argv[1]:
        # ---
        title = sys.argv[1]
        # ---
        work_on_title(title)


def main():
    logger.info("*<<red>> > :")
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
        if not value:
            print(f"Value required for argument {arg}")
            continue
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
        if arg in ["newpages", "-newpages"]:
            newpages = value
        # ---
        if arg in ["-user", "-usercontribs"]:
            user = value
        # ---
        if arg in ["start", "-start"]:
            starts = value
        # ---
        if arg == "-ns":
            namespaces = value
        # ---
        if arg == "search":
            if value in searchlist:
                value = searchlist[value]
            # ---
            ccc = api_new.Search(value=value, ns="0", srlimit="max")
            pages.extend(iter(ccc))
    # ---
    if starts != "":
        # ---
        if starts == "all":
            starts = ""
        # ---
        listen = api_new.Get_All_pages(start=starts, namespace=namespaces, limit=limite)
        # ---
        for n, page in enumerate(listen):
            logger.info(f"<<green>> n:{n}, title:{page}")
            work_on_title(page)
            # ---
    # ---
    lista = []
    # ---
    if newpages != "":
        lista = api_new.Get_Newpages(limit=newpages, namespace=namespaces)
    elif user != "":
        lista = mdwiki_api_call.Get_UserContribs(user, limit=user_limit, namespace=namespaces, ucshow="new")
    elif pages != []:
        lista = pages
    # ---
    for n, page in enumerate(lista):
        logger.info(f"<<green>> n:{n}, title:{page}")
        work_on_title(page)
    # ---


if __name__ == "__main__":
    main()
