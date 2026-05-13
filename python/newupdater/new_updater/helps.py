""" """

import urllib.parse


def ec_de_code(tt, type1):
    fao = tt
    if type1 == "encode":
        # fao = encode_arabic(tt)
        fao = urllib.parse.quote(tt)
    elif type1 == "decode":
        fao = urllib.parse.unquote(tt)
    return fao
