"""
from .bots.expend import expend_infoboxs_and_fix
"""

import wikitextparser as wtp

from ..helps import echo_debug
from ..lists.expend_lists import IMC_params, dup_params


def expend_infoboxs_and_fix(new_text):
    parseds = wtp.parse(new_text)
    # ---
    echo_debug("expend_infoboxs_and_fix")
    # ---
    for template in parseds.templates:
        # ---
        if template:
            name = str(template.normal_name()).strip()
            # ---
            if name.lower() in IMC_params:
                # ---
                _params = list(IMC_params[name.lower()])
                # ---
                dups = dup_params.get(name.lower(), {})
                # ---
                echo_debug("expend_infoboxs_and_fix", f"expend_and_fix: name: {name}")
                # ---
                new_temp = "{{" + name + "\n"
                # ---
                params = {}
                # ---
                for param in template.arguments:
                    na = str(param.name).strip()
                    na = dups.get(na.lower(), na)
                    # ---
                    if na.isdigit() and not str(param.value).strip():
                        continue
                    # ---
                    params[na] = str(param.value)
                # ---
                for x in params:
                    if x not in _params:
                        _params.append(x)
                # ---
                for x in _params:
                    value = params.get(x, "").strip()
                    newparam = f"| {x.ljust(16)}"
                    new_temp += f"{newparam}= {value}\n"
                # ---
                new_temp += "}}"
                # ---
                template.string = new_temp
                # ---
                # temp_text = template.string
                # new_text = new_text.replace(temp_text, new_temp)
                # ---
                del _params, dups, params
    # ---
    new_text = parseds.string
    # ---
    return new_text
