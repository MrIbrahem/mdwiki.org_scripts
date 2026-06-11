import re
import sys

import wikitextparser as wtp

from .make_title_bot import make_title


def change_lay_source(temp):
    # ---
    temp_name = "cite press release"
    # ---
    temp_name = str(temp.normal_name()).strip()
    # ---
    tab = {
        "url": ["layurl", "lay-url"],
        "title": ["laytitle", "lay-title"],
        "date": ["laydate", "lay-date"],
        "source": ["laysource", "lay-source"],
    }
    # ---
    new_tab = {"url": "", "title": "", "date": "", "source": ""}
    # ---
    for x, ys in tab.items():
        for param in ys:
            if temp.has_arg(param):
                val = temp.get_arg(param).value
                if val.strip() != "":
                    new_tab[x] = val.strip()
                temp.del_arg(param)
    # ---
    title = new_tab["title"]
    url = new_tab["url"]
    Date = new_tab["date"]
    source = new_tab["source"]
    # ---
    if title == "" and url != "":
        title = make_title(url)
        title = title.replace("|", "{{!}}")
    # ---
    lay_temp = ""
    # ---
    if url != "" or source != "":
        lay_temp = f"""|template = {temp_name}|url = {url}|title = {title}|date = {Date}|website = {source}"""
        lay_temp = "* {{lay source" + lay_temp + "}}"
    # ---
    return lay_temp, temp


def add_title(temp):
    title = ""
    # ---
    title_arg = temp.get_arg("title")
    # ---
    if title_arg:
        title = str(title_arg.value).strip()
    url = temp.get_arg("url").value if temp.has_arg("url") else ""
    # ---
    if title != "" or url == "":
        return temp
    # ---
    title = make_title(url)
    # ---
    if not title:
        return temp
    # ---
    title = title.replace("|", "{{!}}")
    # ---
    if title_arg:
        title_arg.value = title
    else:
        temp.set_arg("title", title)
    # ---
    return temp


def fix_ref_template(text, returnsummary=False):
    # ---
    summary = "Normalize references"
    # ---
    newtext = text
    # ---
    parsed = wtp.parse(text)
    # ---
    for tag in parsed.get_tags(name="ref"):
        # ---
        content = tag.contents
        # ---
        if not content.strip():
            continue
        # ---
        templates = tag.templates
        # ---
        for temp in templates:
            # ---
            temp_str = temp.string
            # ---
            laysource, temp = change_lay_source(temp)
            # ---
            temp = add_title(temp)
            # ---
            temp_new = temp.string
            # ---
            if "newline" not in sys.argv:
                temp_new = re.sub(r"\n", "", temp_new, flags=re.DOTALL)
            # ---
            if laysource != "":
                temp_new = f"{temp_new}\n{laysource}"
                summary = "Normalize references, move lay source params"
            # ---
            newtext = newtext.replace(temp_str, temp_new)
    # ---
    return (newtext, summary) if returnsummary else newtext


__all__ = [
    "change_lay_source",
    "add_title",
    "fix_ref_template",
]
