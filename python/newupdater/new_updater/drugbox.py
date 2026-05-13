import re

import wikitextparser as wtp

from .helps import echo_debug
from .lists.bot_params import all_formola_params, all_params, params_placeholders, params_to_add

# ---
lkj = r"<!--\s*(Monoclonal antibody data|External links|Names*|Clinical data|Legal data|Legal status|Pharmacokinetic data|Chemical and physical data|Definition and medical uses|Chemical data|Chemical and physical data|index_label\s*=\s*Free Base|\w+ \w+ data|\w+ \w+ \w+ data|\w+ data|\w+ status|Identifiers)\s*-->"
# ---
lkj2 = r"(<!--\s*(?:Monoclonal antibody data|External links|Names*|Clinical data|Legal data|Legal status|Pharmacokinetic data|Chemical and physical data|Definition and medical uses|Chemical data|Chemical and physical data|index_label\s*=\s*Free Base|\w+ \w+ data|\w+ \w+ \w+ data|\w+ data|\w+ status)\s*-->)"
# ---


class TextProcessor:
    def __init__(self, text):
        # ---
        self.text = text
        self.new_text = text

        self.drugbox_params = {}
        self.all_drugbox_params = {}
        self.olddrugbox = ""
        self.drugbox_title = ""
        self.newdrugbox = ""
        # ---
        self.params_done_lowers = []
        # ---
        self.run()

    def get_new_temp(self):
        return self.newdrugbox

    def get_old_temp(self):
        return self.olddrugbox

    def get_txt_params(self, text):
        # ---
        echo_debug("get_txt_params")
        # ---
        txt = ""
        params = {}
        parsed = wtp.parse(text)
        # ---
        for template in parsed.templates:
            # ---
            if not template:
                continue
            # ---
            name = str(template.normal_name()).strip()
            # ---
            medical_infoboxes = [
                "infobox medical condition (new)",
                "infobox medical condition",
            ]
            # ---
            if name.lower() in medical_infoboxes:
                echo_debug("get_txt_params", f"*find temp:[{name}].")
                continue
            # ---
            if name.lower() in ["drugbox", "infobox drug"]:
                # ---
                self.drugbox_title = name
                # ---
                txt = template.string
                # ---
                params = {str(param.name).strip(): str(param.value) for param in template.arguments}
                # ---
                break
        # ---
        return txt, params

    def run(self):
        # ---
        echo_debug("run")
        # ---
        self.olddrugbox, self.drugbox_params = self.get_txt_params(self.text)
        # ---
        if not self.olddrugbox:
            return
        # ---
        drugbox2 = re.sub(lkj2, "", self.olddrugbox)
        # ---
        drugbox2, params = self.get_txt_params(drugbox2)
        # ---
        self.drugbox_params = params
        self.all_drugbox_params = params
        # ---
        # create self.newdrugbox
        self.new_temp()

    def add_section_title_to_sec_text2(self, section_title, sec_text):
        # ---
        if self.newdrugbox.strip().endswith(section_title) or self.newdrugbox.find(section_title) != -1:
            echo_debug("add_section_title_to_sec_text2", f"({section_title}) already in self.newdrugbox \n")
        else:
            sec_text = f"{section_title}\n{sec_text}"
        # ---
        return sec_text

    def add_section_title_to_sec_text(self, section_title, sec_text):
        # ---
        if self.newdrugbox.strip().endswith(section_title):
            # ---
            echo_debug("add_section_title_to_sec_text", f"self.newdrugbox.endswith({section_title}) \n")
            # ---
            title_escape = re.escape(section_title)
            # ---
            self.newdrugbox = re.sub(title_escape, "", self.newdrugbox, flags=re.IGNORECASE)
            # ---
            self.newdrugbox = self.newdrugbox.strip()
        # ---
        if self.newdrugbox.find(section_title) != -1:
            # ---
            echo_debug("add_section_title_to_sec_text", f"self.newdrugbox.find({section_title}) != -1 \n")
            # ---
            title_escape = re.escape(section_title)
            # ---
            self.newdrugbox = re.sub(title_escape, "", self.newdrugbox, flags=re.IGNORECASE)
        # ---
        sec_text = f"{section_title}\n{sec_text}"
        # ---
        return sec_text

    def add_section(self, section):
        # ---
        section_title, sec_text = section[0].strip(), section[1].strip()
        # ---
        if not sec_text:
            return
        # ---
        if section_title:
            sec_text = self.add_section_title_to_sec_text(section_title, sec_text)
        # ---
        s_text = "\n\n" + sec_text
        # ---
        self.newdrugbox += s_text

    def get_combo(self):
        # ---
        echo_debug("get_combo")
        # ---
        combo_titles = {"mab": "Monoclonal antibody data", "vaccine": "Vaccine data", "combo": "Combo data"}
        # ---
        all_combo = all_params["combo"]["all"]
        # ---
        _type = self.drugbox_params.get("type", "").lower().strip()
        # ---
        sec_title = "| type = mab / vaccine / combo"
        # ---
        if _type:
            empty = bool(re.match(r"<!--\s*empty\s*-->", _type))
            # ---
            echo_debug("get_combo", f"{empty=}")
            # ---
            # remove html coments
            _type = re.sub(r"<!--.*?-->", "", _type)
            # ---
            sec_title = combo_titles.get(_type) or sec_title
            # ---
            if _type in combo_titles:
                # ---
                params = all_params["combo"][_type]
                # ---
                for p in all_combo:
                    if p not in params:
                        params.append(p)
                # ---
                all_combo = params
            else:
                echo_debug("get_combo", f" {_type=} not in combo_titles")
            # ---
            if empty:
                sec_title = ""
        # ---
        sec_params = all_combo
        # ---
        echo_debug("get_combo", f" {sec_title=}")
        echo_debug("get_combo", f" all_combo keys: {len(all_combo)=}")
        # ---
        return sec_title, sec_params

    def get_chemical(self):
        # ---
        echo_debug("get_chemical")
        # ---
        sec_params = all_params.get("chemical", {})
        # ---
        sec_text = ""
        # ---
        n = 0
        # ---
        for x in all_formola_params:
            # ---
            if x not in self.drugbox_params:
                continue
            # ---
            x_val = self.drugbox_params.get(x, "").strip()
            # ---
            self.params_done_lowers.append(x.strip().lower())
            # ---
            n += 1
            # ---
            vv = f"| {x}= {x_val} "
            # ---
            if n % 5 == 0:
                vv += "\n"
            # ---
            sec_text += vv
        # ---
        # remove all_formola_params from sec_params
        for p in all_formola_params:
            if p in sec_params:
                sec_params.remove(p)
        # ---
        return sec_text, sec_params

    def create_section(self, sectionname):
        # ---
        sections_titles = {
            "first": "",
            "combo": "",
            "names": "Names",
            "gene": "GENE THERAPY",
            "clinical": "Clinical data",
            "external": "External links",
            "legal": "Legal data",
            "physiological": "Physiological data",
            "pharmacokinetic": "Pharmacokinetic data",
            "chemical": "Chemical and physical data",
            "last": "",
        }
        # ---
        sec_title = sections_titles[sectionname]
        # ---
        sec_params = all_params.get(sectionname, [])
        add_params = params_to_add.get(sectionname, [])
        # ---
        if sectionname == "combo":
            sec_title, sec_params = self.get_combo()
        # ---
        section_title = ""
        # ---
        if sec_title != "":
            section_title = f"<!-- {sec_title} -->"
        # ---
        if sectionname in ["first", "last"]:
            section_title = ""
        # ---
        sec_text = ""
        # ---
        if sectionname == "chemical":
            sec_text, sec_params = self.get_chemical()
        # ---
        if sectionname == "last":
            sec_params = [x for x in self.drugbox_params.keys() if x.lower().strip() not in self.params_done_lowers]
        # ---
        for p in sec_params:
            p = p.strip()
            # ---
            if p in self.drugbox_params or p in add_params:
                p_value = self.drugbox_params.get(p, "").strip()
                # ---
                if not p_value.strip():
                    p_value = params_placeholders.get(p, "").strip()
                # ---
                p2 = p.ljust(18)
                # ---
                self.params_done_lowers.append(p.lower())
                # ---
                p_v = f"\n| {p2}= {p_value}"
                # ---
                sec_text += p_v
        # ---
        # if sec_text != '' and section_title != '': sec_text = f'{section_title}\n{sec_text}'
        # ---
        return [section_title, sec_text]

    def new_temp(self):
        # ---
        self.newdrugbox = "{{" + self.drugbox_title
        # ---
        first_section = self.create_section("first")
        self.add_section(first_section)
        # ---
        combo_section = self.create_section("combo")
        self.add_section(combo_section)
        # ---
        names_section = self.create_section("names")
        self.add_section(names_section)
        # ---
        GENE_section = self.create_section("gene")
        self.add_section(GENE_section)
        # ---
        Clinical_section = self.create_section("clinical")
        self.add_section(Clinical_section)
        # ---
        External_links_section = self.create_section("external")
        self.add_section(External_links_section)
        # ---
        Legal_section = self.create_section("legal")
        self.add_section(Legal_section)
        # ---
        Physiological_section = self.create_section("physiological")
        self.add_section(Physiological_section)
        # ---
        Pharmacokinetic_section = self.create_section("pharmacokinetic")
        self.add_section(Pharmacokinetic_section)
        # ---
        Chemical_section = self.create_section("chemical")
        self.add_section(Chemical_section)
        # ---
        last_section = self.create_section("last")
        self.add_section(last_section)
        # ---
        self.newdrugbox += "\n}}"
