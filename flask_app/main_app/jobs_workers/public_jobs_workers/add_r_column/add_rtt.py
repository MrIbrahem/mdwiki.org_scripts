#!/usr/bin/python3
""" """

import logging

import tqdm
import wikitextparser as wtp

logger = logging.getLogger(__name__)

R_NEW_ROW = '\n| style="text-align:center; white-space:nowrap; font-weight:bold; background:#C66A05" | R'


def fix_title(title):
    title = title.replace("[[", "").replace("]]", "")
    title = title.replace("&#039;", "'")

    return title


def header_has_r(text, table=False):
    if not table:
        parsed = wtp.parse(text)
        table = parsed.tables[0]

    # for table in parsed.tables:

    for x in table.cells():
        if x[1].is_header:
            for numb, v in enumerate(x, 1):
                if v.value.strip() == "R":
                    logger.info(f"header has R: in column {numb}")
                    return True

    return False


def add_header_r(text, table=False):
    if not table:
        parsed = wtp.parse(text)
        table = parsed.tables[0]

    # for table in parsed.tables:

    # Check if R column already exists
    if header_has_r(text, table):
        logger.info("R column already exists in table header")
        return table.string

    count = 0

    # add R to header in 2nd column
    for x in table.cells():
        if x[0].is_header:
            x[0].value = x[0].value + "\n! R"
        else:
            x[0].value = x[0].value + "\n| "

        count += 1

    logger.info(f"Added R column to table header in {count} cells")

    return table.string


def work_one_table(table_text, redirects, pages):
    parsed = wtp.parse(table_text)
    table = parsed.tables[0]

    if not header_has_r(table_text, table):
        logger.info("<<red>> no R in table header!")
        return table_text

    already_in = []
    no_add = []

    add_from_redirect = []
    add_done = []

    cell_errors = []

    data = table.data()

    for n, x in enumerate(tqdm.tqdm(table.cells())):
        if x[1].is_header or len(x) < 3:
            continue

        try:
            title = x[2].value.strip()
            r_s = x[1].value.strip()
        except Exception:
            logger.warning(f"cell error: {n}")
            numb = data[n][2]
            cell_errors.append(numb)
            continue

        title = fix_title(title)

        title2 = redirects.get(title, title)

        if r_s == "R":
            x[1].string = R_NEW_ROW

            already_in.append(title)
            continue

        # logger.info(f"title: ({title}), r_s: ({r_s})")

        if title in pages:
            x[1].string = R_NEW_ROW

            add_done.append(title)
        elif title2 in pages:
            x[1].string = R_NEW_ROW

            add_from_redirect.append(title)
        else:
            no_add.append(title)

    logger.info(f"<<yellow>> no_add: {len(no_add)}, already_in: {len(already_in)}")

    logger.error(f"<<red>> cell_errors: {len(cell_errors)}:")
    logger.info(cell_errors)

    logger.info(f"<<yellow>> add_done: {len(add_done)}, add_from_redirect: {len(add_from_redirect)}")

    return table.string


__all__ = [
    "R_NEW_ROW",
    "add_header_r",
    "fix_title",
    "header_has_r",
    "work_one_table",
]
