#!/usr/bin/python3
""" """
import os
import sys

import requests
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception:
    pass

username = os.getenv("WIKIPEDIA_HIMO_USERNAME")
password = os.getenv("MDWIKI_HIMO_PASSWORD")
user_agent = "WikiProjectMed Translation Dashboard/1.0 (https://mdwiki.toolforge.org/; tools.mdwiki@toolforge.org)"

session = {}
session[1] = requests.Session()
session[1].headers.update({"User-Agent": user_agent})
# ---
session["token"] = ""
# ---
session["url"] = "https://mdwiki.org/w/api.php"
# session["url"] = "https://www.mdwiki.org/w/api.php"


def print_s(s):
    if "from_toolforge" not in sys.argv:
        print(s)


def debug_print(s):
    if "from_toolforge" not in sys.argv:
        print(s, "</br>")


def login():
    # ---
    # get login token
    try:
        r1 = session[1].get(
            session["url"],
            params={
                "format": "json",
                "action": "query",
                "meta": "tokens",
                "type": "login",
            },
            timeout=10,
        )
        r1.raise_for_status()
    except Exception as e:
        debug_print(f"login to mdwiki.org Error {e}")
        return False
    # ---
    try:
        r2 = session[1].post(
            session["url"],
            data={
                "format": "json",
                "action": "login",
                "lgname": username,
                "lgpassword": password,
                "lgtoken": r1.json()["query"]["tokens"]["logintoken"],
            },
            timeout=10,
        )
    except Exception as e:
        debug_print(f"login to mdwiki.org Error {e}")
        return False
    # ---
    print_s(r2)
    # ---
    if r2.json()["login"]["result"] != "Success":
        print_s(r2.json()["login"]["reason"])
        # raise RuntimeError(r2.json()['login']['reason'])
        return False
    else:
        print_s("wpref.py login Success to mdwiki.org")
    # ---
    # if r2.json()['login']['result'] != 'Success': debug_print(r2.json()['login']['reason'])
    # raise RuntimeError(r2.json()['login']['reason'])
    # get edit token
    try:
        r3 = session[1].get(
            session["url"],
            params={
                "format": "json",
                "action": "query",
                "meta": "tokens",
            },
            timeout=10,
        )
    except Exception as e:
        debug_print(f"login to mdwiki.org Error {e}")
        return False
    # ---
    token = r3.json()["query"]["tokens"]["csrftoken"]
    # ---
    session["token"] = token


def submitAPI(params, _type="post", add_token=False):
    # ---
    login()
    # ---
    json1 = {}
    # ---
    if add_token or ("token" in params and params["token"] == ""):
        params["token"] = session["token"]
    # ---
    try:
        method = "POST"  # if _type == "post" else "GET"
        # ---
        r4 = session[1].request(method, session["url"], data=params, timeout=10)
        json1 = r4.json()
        # ---
    except Exception as e:
        debug_print(f"submitAPI Error {e}")
        debug_print(params)
        return json1
    # ---
    return json1


def get_revisions(title, lang=""):
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "formatversion": "2",
        "rvprop": "comment|user|timestamp",
        "rvdir": "newer",
        "rvlimit": "max",
    }
    # ---
    rvcontinue = "x"
    # ---
    revisions = []
    # ---
    while rvcontinue != "":
        # ---
        if rvcontinue != "x":
            params["rvcontinue"] = rvcontinue
        # ---
        json1 = submitAPI(params, _type="post")
        # ---
        if not json1 or not isinstance(json1, dict):
            return ""
        # ---
        rvcontinue = json1.get("continue", {}).get("rvcontinue", "")
        # ---
        pages = json1.get("query", {}).get("pages", [{}])
        # ---
        for p in pages:
            _revisions = p.get("revisions", [])
            revisions.extend(_revisions)
    # ---
    return revisions


def GetPageText(title, lang="", print_text=True):
    # ---
    params = {
        "action": "parse",
        "format": "json",
        # "prop": "wikitext|sections",
        "prop": "wikitext",
        "page": title,
        # "redirects": 1,
        "utf8": 1,
        # "normalize": 1,
    }
    # ---
    json1 = submitAPI(params, _type="post")
    # ---
    if not json1 or not isinstance(json1, dict):
        if print_text:
            print_s("json1 ==:")
            print_s(json1)
        return ""
    # ---
    if not json1:
        if print_text:
            print_s("json1 == {}")
        return ""
    # ---
    _err = json1.get("error", {}).get("code", {})
    # ---
    parse = json1.get("parse", {})
    if not parse:
        if print_text:
            print_s("parse == {}")
            print_s(json1)
        return ""
    # ---
    text = parse.get("wikitext", {}).get("*", "")
    # ---
    if not text:
        if print_text:
            print_s(f'page {title} text == "".')
    # ---
    return text


def page_put(new_text, summary, title):
    # ---
    if not session["token"]:
        print_s("login error, token empty.")
        return {}
    # ---
    pparams = {
        "action": "edit",
        "format": "json",
        # "maxlag": ar_lag[1],
        "title": title,
        "text": new_text,
        "summary": summary,
        # "starttimestamp": starttimestamp,
        # "minor": minor,
        # "notminor": 1,
        "bot": 1,
        "nocreate": 1,
        "token": session["token"],
    }
    # ---
    json1 = submitAPI(pparams, add_token=True)
    # ---
    if not json1:
        return ""
    # ---
    if "Success" in str(json1):
        print_s(f"<<green>> ** true .. [[mdwiki:{title}]]")
        return True
    # ---
    else:
        print_s(json1)
    # ---
    return False


if __name__ == "__main__":
    login()
