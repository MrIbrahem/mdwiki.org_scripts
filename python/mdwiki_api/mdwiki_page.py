""" """

import functools
import os

from flask_app.main_app.newapi import AllAPIS

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


main_api = load_main_api()

NewApi = main_api.NewApi
MainPage = main_api.MainPage
CatDepth = main_api.CatDepth
md_MainPage = MainPage  # noqa: N816

__all__ = [
    "MainPage",
    "md_MainPage",
    "NewApi",
    "CatDepth",
]
