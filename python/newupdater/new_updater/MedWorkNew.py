#!/usr/bin/python3
"""
python3 pwb.py newupdater/med Aspirin from_toolforge
python3 pwb.py newupdater/med Retinol from_toolforge

"""
import re

# ---
from .bots import expend  # expend_infoboxs_and_fix(text)
from .bots import expend_new  # expend_infoboxs(text)
from .bots import old_params
from .chembox import fix_Chembox
from .drugbox import TextProcessor
from .helps import echo_debug
from .mv_section import move_External_links_section
from .resources_new import move_resources

# ---
lkj = r"<!--\s*(Monoclonal antibody data|External links|Names*|Clinical data|Legal data|Legal status|Pharmacokinetic data|Chemical and physical data|Definition and medical uses|Chemical data|Chemical and physical data|index_label\s*=\s*Free Base|\w+ \w+ data|\w+ \w+ \w+ data|\w+ data|\w+ status|Identifiers)\s*-->"
# ---
lkj2 = r"(<!--\s*(?:Monoclonal antibody data|External links|Names*|Clinical data|Legal data|Legal status|Pharmacokinetic data|Chemical and physical data|Definition and medical uses|Chemical data|Chemical and physical data|index_label\s*=\s*Free Base|\w+ \w+ data|\w+ \w+ \w+ data|\w+ data|\w+ status)\s*-->)"


def drugbox_work(new_text, text):
    # ---
    echo_debug("drugbox_work")
    # ---
    # new_text = re.sub(r'<!--\s*\|\s*type\s*=\s*mab\s*\/\s*vaccine\s*\/\s*combo\s*-->', '<!-- type = mab / vaccine / combo -->', new_text, flags=re.IGNORECASE)
    # ---
    bot = TextProcessor(new_text)
    # ---
    drugbox_text = bot.get_old_temp()
    drug_box_new = bot.get_new_temp()
    # ---
    if not drugbox_text:
        echo_debug("drugbox_work", "no drugbox_text")
        return new_text
    # ---
    if not drug_box_new:
        echo_debug("drugbox_work", "no drug_box_new")
        return new_text
    # ---
    drug_box_new = re.sub(rf"\s*{lkj2}\s*", r"\n\n\g<1>\n", drug_box_new, flags=re.DOTALL)
    # ---
    drug_box_new = re.sub(r"\n\s*\n\s*[\n\s]+", "\n\n", drug_box_new, flags=re.DOTALL | re.MULTILINE)
    # ---
    drug_box_new = re.sub(
        r"{{(Infobox drug|Drugbox|drug resources)\s*\n*", r"{{\g<1>\n", drug_box_new, flags=re.DOTALL | re.MULTILINE
    )
    # ---
    if new_text.find(drugbox_text) == -1 and new_text.find(drugbox_text.strip()) == -1:
        echo_debug("drugbox_work", "can't find old (drugbox_text) in new_text, return original text")
        return new_text
    # ---
    # replace the old drugbox by newdrugbox
    new_text = new_text.replace(drugbox_text, drug_box_new)
    # ---
    new_text = re.sub(
        r"\{\{(Infobox drug|Drugbox|drug resources)\s*\<\!", r"{{\g<1>\n<!", new_text, flags=re.IGNORECASE
    )
    # ---
    return new_text


def work_on_text_md(title, text):
    # ---
    echo_debug("work_on_text_md")
    # ---
    new_text = text
    # ---
    new_text = old_params.rename_params(new_text)
    # ---
    new_text = move_resources(new_text, title, lkj=lkj, lkj2=lkj2)
    # ---
    new_text = drugbox_work(new_text, text)
    # ---
    bot2 = move_External_links_section(new_text)
    # ---
    new_text = bot2.make_new_txt()
    # ---
    new_text = re.sub(r"\n\s*\[\[Category", "\n[[Category", new_text, flags=re.DOTALL | re.MULTILINE)
    # ---
    return new_text


def work_on_text(title, text):
    # ---
    echo_debug("work_on_text")
    # ---
    newtext = text
    # ---
    Chem = re.search(r"{{(Chembox)", newtext, flags=re.IGNORECASE)
    # ---
    if Chem:
        bot = fix_Chembox(newtext)
        newtext = bot.run()
    # ---
    rea = re.search(r"{{(Infobox drug|Drugbox)", newtext, flags=re.IGNORECASE)
    # ---
    if not rea:
        newtext = expend_new.expend_infoboxs(newtext)
        newtext = expend.expend_infoboxs_and_fix(newtext)
        # ---
        # return newtext
    # ---
    newtext = work_on_text_md(title, newtext)
    # ---
    return newtext
