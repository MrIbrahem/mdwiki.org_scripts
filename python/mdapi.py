#!/usr/bin/python3
""" """
import functools
import logging
import os

from flask_app.main_app.newapi import AllAPIS

logger = logging.getLogger(__name__)


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


def post_s(params) -> dict:
    main_api = load_main_api()
    params["format"] = "json"
    params["utf8"] = 1
    # ---
    json1 = main_api.login_bot.client_request_safe(params)
    # ---
    return json1


def GetPageText(title, lang="", print_text=True):
    main_api = load_main_api()
    page = main_api.MainPage(title, "www", family="mdwiki")
    return page.get_text()


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
