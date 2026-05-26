#!/usr/bin/python3
""" """

import logging
from functools import lru_cache

import wikitextparser as wtp

logger = logging.getLogger(__name__)


@lru_cache(maxsize=512)
def extract_templates_and_params(text):
    # ---
    result = []
    # ---
    parsed = wtp.parse(text)
    templates = parsed.templates
    arguments = "arguments"
    # ---
    for template in templates:
        # ---
        params = {}
        for param in getattr(template, arguments):
            value = str(param.value)  # mwpfh needs upcast to str
            key = str(param.name)
            key = key.strip()
            params[key] = value
        # ---
        name = template.name.strip()
        # ---
        # print('=====')
        # ---
        name = str(template.normal_name()).strip()
        pa_item = template.string
        # logger.info( "<<lightyellow>> pa_item: %s" % pa_item )
        # ---
        namestrip = name
        # ---
        ficrt = {
            "name": f"قالب:{name}",
            "namestrip": namestrip,
            "params": params,
            "item": pa_item,
        }
        # ---
        result.append(ficrt)
    # ---
    return result
