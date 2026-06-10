#!/usr/bin/python3
"""
Change refs to newlines
python3 core8/pwb.py md_core/mdpy/fixref
"""

import logging
import os
import sys

from python.mdwiki_page import CatDepth, NewApi, load_main_api

from src.main_app.shared.fixref_shared.fixref_text_new import fix_ref_template

logger = logging.getLogger(__name__)

if os.getenv("HOME"):
    public_html_dir = os.getenv("HOME") + "/public_html"
else:
    public_html_dir = "I:/MD_TOOLS/MDWIKI_MAIN_REPO/public_html"
# ---
thenumbers = {1: 20000, "done": 0}


def work(title):
    # ---
    main_api = load_main_api()
    # ---s
    page = main_api.MainPage(title, "www", family="mdwiki")
    _exists = page.exists()
    # ---
    text = page.get_text()
    # ---
    summary = "Normalize references"
    # ---
    new_text, summary = fix_ref_template(text, returnsummary=True)
    # ---
    if new_text != text:
        thenumbers["done"] += 1
        # ---
        page.save(newtext=new_text, summary=summary)
        # ---
    else:
        logger.info("no changes.")


def main():
    # ---
    api_new = NewApi("www", family="mdwiki")
    List = []
    # ---
    for arg in sys.argv:
        arg, _, value = arg.partition(":")
        # ---
        if arg == "-number" and value.isdigit():
            thenumbers[1] = int(value)
        # ---
        if arg == "-file":
            text = open(f"{public_html_dir}/find/{value.strip()}", "r", "utf8").read()
            List = [x.strip() for x in text.split("\n") if x.strip() != ""]
        # ---
        if arg == "allpages":
            List = api_new.Get_All_pages("")
        # ---
        # python pwb.py md_core/mdpy/fixref/start -cat:CS1_errors:_deprecated_parameters ask
        if arg == "-cat":
            List = CatDepth(f"Category:{value}", sitecode="www", family="mdwiki", depth=0, ns="0")
        # ---
        # python pwb.py md_core/mdpy/fixref/start -page:Histrelin ask
        if arg in ["-page", "-title"]:
            List = [value]
            # ---
    # ---
    num = 0
    for title in List:
        num += 1
        # ---
        if thenumbers["done"] >= thenumbers[1] and len(List) > 1:
            break
        work(title)


if __name__ == "__main__":
    main()
