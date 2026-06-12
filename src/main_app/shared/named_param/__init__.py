import logging
from typing import Any

import wikitextparser as wtp

logger = logging.getLogger(__name__)


def gt_arg(temp: wtp.Template, name: str) -> str | bool:
    if temp.has_arg(name):
        va = temp.get_arg(name)
        if va and va.value and va.value.strip():
            return va.value.strip()
    return False


def add_param_named(text: str) -> str:
    parsed = wtp.parse(text)

    param = "named after"
    target_infoboxs = [
        "infobox medical condition",
        "infobox medical condition (new)",
    ]

    _false_params_old = [
        "named after",
        "eponym",
    ]
    # ---
    false_params: list[Any] = list(_false_params_old)

    for temp in parsed.templates:
        name = str(temp.normal_name()).strip().lower().replace("_", " ")
        if name in target_infoboxs:
            # ---
            if temp.has_arg(param):
                arg = temp.get_arg(param)
                value = arg.value if arg else ""
                logger.info(f"page already had temp {name} with (|{param}={value}). ")
                return text
            # ---
            for x in false_params:
                value = gt_arg(temp, x)
                if value:
                    logger.info(f"page already had temp {name} with (|{x}={value}). ")
                    return text
            # ---
            t_value = ""
            # ---
            if temp.has_arg("eponym"):
                if gt_arg(temp, "eponym"):
                    t_value = gt_arg(temp, "eponym")
                # ---
                temp.del_arg("eponym")
            # ---
            temp.set_arg(f" {param} ", f" {t_value}\n")

    newtext = parsed.string

    return newtext


__all__ = [
    "gt_arg",
    "add_param_named",
]
