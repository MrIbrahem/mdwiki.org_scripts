import re

import wikitextparser

from .helps import echo_debug


class move_External_links_section:
    def __init__(self, text):
        self.text = text
        # ---
        self.new_text = self.text
        self.text_to_work = self.text
        # ---
        self.parser = wikitextparser.parse(self.text)
        # ---
        self.sections = self.parser.get_sections(include_subsections=True)
        # ---
        self.ext_sec = ""
        self.new_ext_sec = ""
        self.last_sec = ""
        # ---
        self.run()

    def run(self):
        # ---
        echo_debug("move_External_links_section: run")
        # ---
        self.get_sects()
        # ---
        if not self.ext_sec:
            return
        # ---
        if str(self.ext_sec) == str(self.last_sec):
            return
        # ---
        self.add_ext_section()

    def add_ext_section(self):
        # ---
        echo_debug("add_ext_section")
        # ---
        categoryPattern = r"\[\[\s*(Category)\s*:[^\n]*\]\]\s*"
        interwikiPattern = r"\[\[([a-zA-Z\-]+)\s?:([^\[\]\n]*)\]\]\s*"
        templatePattern = r"\r?\n{{((?!}}).)+?}}\s*"
        commentPattern = r"<!--((?!-->).)*?-->\s*"
        # ---
        # metadataR = re.compile(fr'(\r?\n)?({categoryPattern}|{interwikiPattern}|{commentPattern})$', re.DOTALL)
        metadataR = re.compile(
            rf"(\r?\n)?({categoryPattern}|{interwikiPattern}|{templatePattern}|{commentPattern})$", re.DOTALL
        )
        # ---
        tmpText = self.text_to_work
        # ---
        while True:
            if match := metadataR.search(tmpText):
                tmpText = tmpText[: match.start()]
            else:
                break
        # ---
        index = len(tmpText)
        # ---
        newtext = (
            f"{self.text_to_work[:index].rstrip()}\n\n{self.new_ext_sec.strip()}\n\n{self.text_to_work[index:].strip()}"
        )
        # ---
        self.new_text = newtext

    def get_sects(self):
        # ---
        echo_debug("get_sects")
        # ---
        last = ""
        # ---
        for n, s in enumerate(self.sections, start=-1):
            # ---
            t = s.title
            c = s.contents
            # ---
            if t and t.strip().lower() == "external links":
                self.ext_sec = str(s)
                self.new_ext_sec = str(s)
                # ---
            # ---
            last = s
            # ---
        # ---
        if not self.ext_sec:
            return
        # ---
        self.text_to_work = self.text_to_work.replace(str(self.ext_sec), "")
        # ---
        self.last_sec = last
        # ---
        if self.last_sec.title.lower().strip() == "references":
            l_c = self.last_sec.contents
            # ---
            echo_debug("get_sects", f"title: {self.last_sec.title}")
            echo_debug("get_sects", f"contents: {l_c}")
            # ---
            mata = re.search(r"^{{reflist(?:[^{]|{[^{]|{{[^{}]+}}|)+}}", l_c, flags=re.IGNORECASE)
            # ---
            if mata:
                # ---
                # ---
                index = len(l_c[: mata.end()])
                # ---
                l_c2 = l_c[index:]
                # ---
                # echo_debug("get_sects", f'index : {index}')
                # echo_debug("get_sects", f'l_c2 : {l_c2}')
                # ---
                g = mata.group()
                g_to = f"== {self.last_sec.title.strip()} ==\n{g}\n"
                # ---
                echo_debug("get_sects", f"g_to: {g_to}")
                # ---
                self.ext_sec = f"{g_to}\n{self.ext_sec}"
                self.new_ext_sec = self.ext_sec
                # ---
                self.text_to_work = self.text_to_work.replace(str(self.last_sec).strip(), l_c2.strip())

    def make_new_txt(self):
        # ---
        echo_debug("make_new_txt")
        # ---
        self.new_text = re.sub(r"\n\s*\[\[Category", "\n[[Category", self.new_text, flags=re.DOTALL | re.MULTILINE)
        # ---
        return self.new_text
