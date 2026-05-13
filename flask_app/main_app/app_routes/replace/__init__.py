""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

bp_replace = Blueprint("main", __name__, url_prefix="/replace")
logger = logging.getLogger(__name__)

AUTHORIZED_USERS = ["Doc James", "Mr. Ibrahem"]


@bp_replace.route("/", methods=["GET", "POST"])
def replace():
    listtype = request.values.get("listtype", "newlist")
    test = request.values.get("test", "")
    find = request.values.get("find", "")
    replace_ = request.values.get("replace", "")
    number = request.values.get("number", "")

    result = None
    if request.method == "POST" and find and replace_:
        logger.info(f"replace triggered: listtype={listtype}, number={number}")
        # TODO: integrate find_replace_bot backend directly (pass data in-memory, not via files)
        result = f"Find & Replace job started (listtype={listtype})"
        if number:
            result += f" with max {number} replacements"
        if test:
            result = f"[TEST] {result}"

    return render_template(
        "replace.html",
        listtype=listtype,
        test=test,
        find=find,
        replace=replace_,
        number=number,
        result=result,
    )


__all__ = ["bp_replace"]
