"""
from .bots.old_params import rename_params
"""

import logging

import wikitextparser as wtp

logger = logging.getLogger(__name__)


def rename_params(temptext):
    # ---
    logger.debug("rename_params")
    # ---
    to_replace = {
        "side effects": "side_effects",
        # "routes_of_use" : "routes_of_administration",
        "side effect": "side_effects",
        "side_effect": "side_effects",
        "legal status": "legal_status",
        "smiles": "SMILES",
        "smiles2": "SMILES2",
    }
    # ---
    new_temptext = temptext
    # ---
    # Parse the wikitext
    parsed_old = wtp.parse(new_temptext)
    temps = parsed_old.templates
    # ---
    temps_okay = ["drugbox", "infobox drug"]
    # ---
    _temps_ = []
    # ---
    for temp in temps:
        # ---
        name = temp.normal_name()
        # ---
        if str(name).lower() in temps_okay:
            _temps_.append(temp)
        else:
            logger.debug(f"rename_params {name=} not in temps_okay .")
    # ---
    if not _temps_:
        logger.debug("_temps_ is empty")
        return new_temptext
    # ---
    for temp in _temps_:
        old_temp = temp.string
        # ---
        if new_temptext.find(old_temp) == -1:
            logger.debug(f"*+new_temptext find ({[old_temp]}) == -1 .")
            continue
        # ---
        # Replace the old parameter with the new parameter
        for old, new in to_replace.items():
            if temp.has_arg(old):
                value = temp.get_arg(old).value
                logger.debug(f"value: {value}")
                temp.set_arg(new, value, before=old)
                temp.del_arg(old)
        # ---
        new_temptext = new_temptext.replace(old_temp, temp.string)
    # ---
    return new_temptext
