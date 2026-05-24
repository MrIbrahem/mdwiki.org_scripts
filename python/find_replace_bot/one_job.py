#!/usr/bin/python3
"""

from md_core.mdpy.find_replace_bot.one_job import do_one_job
"""
import json
import logging
import os
import sys
from pathlib import Path

import tqdm
from python.mdwiki_page import MainPage, NewApi

logger = logging.getLogger(__name__)


home_dir = os.getenv("HOME")

dir2 = home_dir if home_dir else "I:/MD_TOOLS/MDWIKI_MAIN_REPO"

work_dir = f"{dir2}/public_html/replace/find"

api_new = NewApi("www", family="mdwiki")


def write_text(text_file, line, w_or_a="w"):
    if w_or_a == "a" and not os.path.exists(text_file):
        w_or_a = "w"
    try:
        with open(text_file, w_or_a, encoding="utf-8") as file:
            file.write(line)
    except Exception as e:
        logger.info(f"write_text error:{e}")


def work(title, Find, Replace, nn, log_file):
    # ---
    page = MainPage(title, "www", family="mdwiki")
    # ---
    exists = page.exists()
    # ---
    if not exists:
        return 0
    # ---
    text = page.get_text()
    # ---
    if not text.strip():
        logger.info(f"page:{title} text = ''")
        line = '"%s":"no changes",\n' % title.replace('"', '\\"')
        # ---
        write_text(log_file, line, w_or_a="a")
        # ---
        return 0
    # ---
    new_text = text
    # ---
    if "testtest" in sys.argv:
        new_text = new_text.replace(Find, Replace, 1)
    else:
        new_text = new_text.replace(Find, Replace)
    # ---
    if new_text == text:
        line = '"%s":"no changes",\n' % title.replace('"', '\\"')
        # ---c
        # ---
        return 0
    # ---
    revid = page.get_revid()
    # ---
    sus = f"replace {nn} [[toolforge:mdwiki/qdel.php?job=replace{nn}|(stop)]] "
    # ---
    save_page = page.save(newtext=new_text, summary=sus)
    # ---
    line = '"%s":%d,\n' % (title.replace('"', '\\"'), 0)
    # ---
    if save_page:
        # ---
        newrevid = page.get_newrevid()
        # ---
        if newrevid not in [revid, ""]:
            # ---
            line = '"%s":%d,\n' % (title.replace('"', '\\"'), newrevid)
        # ---
        write_text(log_file, line, w_or_a="a")
        # ---
        return 1
    # ---
    return 0


def check_for_stop(nn, text_file):
    # ---
    stop_file = f"{work_dir}/{nn}/stop.txt"
    # ---
    if Path(stop_file).exists():
        line = "<span style='font-size:12px; color:red'>This job was stopped by stop button.</span>"
        # ---
        write_text(text_file, line)
        # ---
        return True
    # ---
    return False


def do_one_job(nn):
    # ---
    logger.info(nn)
    # ---
    info_file = f"{work_dir}/{nn}/info.json"
    # ---
    nn_info = {}
    # ---
    if Path(info_file).exists():
        try:
            with open(Path(info_file), "r", encoding="utf-8") as file:
                nn_info = json.load(file)
        except Exception as e:
            logger.info(f"can't load {info_file}, {e}")
    # ---
    log_file = f"{work_dir}/{nn}/log.txt"
    text_file = f"{work_dir}/{nn}/text.txt"
    # ---
    find, replace = get_find_and_replace(nn)
    # ---
    # write_text(Path(log_file), "")
    # ---
    listtype = nn_info.get("listtype", "")
    max_numbers = nn_info.get("number", "0")
    # ---
    if max_numbers.isdigit():
        max_numbers = int(max_numbers)
    else:
        max_numbers = 1000000
    # ---
    titles = get_titles(find, listtype)
    # ---
    line = f"<span style='font-size:12px'>start work in {len(titles)} pages.</span>"
    # ---
    write_text(text_file, line)
    # ---
    numbers_done = 0
    # ---
    for n, page in tqdm.tqdm(enumerate(titles, start=1)):
        # ---
        if n % 10 == 0:
            stop = check_for_stop(nn, text_file)
            if stop:
                break
        # ---
        if numbers_done >= max_numbers and max_numbers > 0:
            break
        # ---
        result = work(page, find, replace, nn, log_file)
        # ---
        if result:
            numbers_done += 1
    # ---
    if numbers_done:
        done_file = f"{work_dir}/{nn}/done.txt"
        # ---
        write_text(done_file, "done")


def get_titles(find, listtype):
    # ---
    if listtype == "newlist":
        Add_pa = {"srsort": "just_match", "srwhat": "text"}
        titles = api_new.Search(value=find, ns="0", srlimit="max", return_dict=False, addparams=Add_pa)
    else:
        titles = api_new.Get_All_pages()
    # ---
    return titles


def get_find_and_replace(nn):
    # ---
    find_file = f"{work_dir}/{nn}/find.txt"
    replace_file = f"{work_dir}/{nn}/replace.txt"
    # ---
    find = ""
    replace = ""
    # ---
    try:
        with open(find_file, "r", encoding="utf-8") as file:
            find = file.read()
    except Exception as e:
        logger.info(f"Error reading find file: {e}")
        # return
    # ---
    try:
        with open(replace_file, "r", encoding="utf-8") as file:
            replace = file.read()
    except Exception as e:
        logger.info(f"Error reading replace file: {e}")
        # return
    # ---
    if replace.strip() == "empty":
        replace = ""
    # ---
    return find, replace
