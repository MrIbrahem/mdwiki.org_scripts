#!/usr/bin/python3
"""
python3 I:/MD_TOOLS/mdwiki.toolforge.org/PYTHON_REPOS/pybot/src/newupdater.py -page:Aspirin from_toolforge
"""
import sys

from mdapi import GetPageText, page_put

from src.main_app.shared.new_updater import med_updater_one


def get_new_text(title):
    # ---
    # if not text:
    text = GetPageText(title)
    # ---
    newtext = text
    # ---
    if newtext != "":
        newtext = med_updater_one(title, newtext)
    # ---
    return text, newtext


def save_cash(title, new_text):
    # ---
    title2 = title
    title2 = title2.replace(":", "-").replace("/", "-").replace(" ", "_")
    # ---
    filename = f"updatercash/{title2}_1.txt"
    # ---
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(new_text)
    except Exception:
        filename = "updatercash/title2.txt"
        # ---
        with open(filename, "w", encoding="utf-8") as f:
            f.write(new_text)
    # ---
    return filename


def work_on_title(title):
    # ---
    text, new_text = get_new_text(title)
    # ---
    if text.strip() == "" or new_text.strip() == "":
        return "notext", ""
    # ---
    if text == new_text:
        return "no changes", ""
    # ---
    if not new_text:
        return "notext", ""
    # ---
    return "", new_text


def work(title):
    # ---
    if title == "":
        return "no page"
    # ---
    err, new_text = work_on_title(title)
    # ---
    if err and not new_text:
        return err
    # ---
    if "save" in sys.argv:
        a = page_put(new_text, "Med updater.", title)
        if a:
            return "save ok"
    # ---
    file = save_cash(title, new_text)
    # ---
    return file


def main():
    # ---
    title = ""
    # ---
    for arg in sys.argv:
        arg, _, value = arg.partition(":")
        # ---
        if arg in ["-page", "page"]:
            title = value.replace("_", " ")
    # ---
    result = work(title)
    # ---
    print(result)


if __name__ == "__main__":
    main()
