""" """

import logging

import wikitextparser as wtp

from .lists.chem_params import rename_chem_params

logger = logging.getLogger(__name__)


class FixChembox:
    def __init__(self, text: str) -> None:
        self.text = text
        self.new_text = text

        self.all_params = {}
        self.oldchembox = ""
        self.newchembox_list = ["{{drugbox"]

    def run(self):
        # ---
        logger.debug("FixChembox: run")
        # ---
        self.get_params()
        # ---
        if not self.all_params:
            return self.new_text
        # ---
        self.new_temp()
        # ---
        new_tmp_text = "\n".join(self.newchembox_list)
        # ---
        if self.oldchembox != "" and new_tmp_text != "":
            self.new_text = self.new_text.replace(self.oldchembox, new_tmp_text)
        # ---
        return self.new_text

    def get_params(self) -> None:
        # ---
        parsed = wtp.parse(self.text)
        # ---
        for template in parsed.templates:
            # ---
            if not template:
                continue
            # ---
            name = str(template.normal_name()).strip()
            # ---
            boxes = [
                "chembox",
                "chembox identifiers",
                "chembox properties",
                "chembox hazards",
                "chembox thermochemistry",
                "chembox explosive",
                "chembox pharmacology",
                "chembox related",
                "chembox structure",
                "chembox supplement",
            ]
            # ---
            if name.lower() == "chembox":
                self.oldchembox = template.string
            # ---
            # if name.lower().startswith("chembox"):
            elif name.lower() not in boxes:
                continue
            # ---
            params = {str(param.name).strip(): str(param.value) for param in template.arguments}
            # ---
            for x, v in params.items():
                if not v.strip():
                    continue
                # ---
                if x.lower().startswith("section"):
                    continue
                # ---
                self.all_params[x] = v

    def new_temp(self) -> None:
        # ---
        for p, value in self.all_params.items():
            param = rename_chem_params.get(p, "") if rename_chem_params.get(p, "") != "" else p

            param_value = f"| {param}= {value}" if value.strip() else f"| {param}="

            self.newchembox_list.append(param_value.strip())

        self.newchembox_list.append("}}")


__all__ = [
    "FixChembox",
]
