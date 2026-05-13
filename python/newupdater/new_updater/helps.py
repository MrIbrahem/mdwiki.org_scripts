"""
from .helps import print_s, ec_de_code, echo_debug
"""

import os
import sys
import urllib.parse

DEBUG = os.getenv("DEBUGNEW", "false").lower() == "true"


def print_s(s):
    if "from_toolforge" not in sys.argv:
        print(s)


def echo_debug(func_name="", message=""):
    if not DEBUG:
        return
    # ---
    if message:
        print("\t>>>", message)
    else:
        print("|> DEBUG ", f"def {func_name}():\t", message)


def ec_de_code(tt, type1):
    fao = tt
    if type1 == "encode":
        # fao = encode_arabic(tt)
        fao = urllib.parse.quote(tt)
    elif type1 == "decode":
        fao = urllib.parse.unquote(tt)
    return fao
