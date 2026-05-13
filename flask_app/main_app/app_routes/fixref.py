"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

bp_fixref = Blueprint("main", __name__, url_prefix="/fixref")
logger = logging.getLogger(__name__)


@bp_fixref.route("/", methods=["GET", "POST"])
def fixref():
    titlelist = request.values.get("titlelist", "")
    number = request.values.get("number", "")
    test = request.values.get("test", "")

    result = None
    if request.method == "POST":
        if titlelist and number:
            logger.info(f"fixref triggered: titlelist={bool(titlelist)}, number={number}")
            # TODO: integrate fixref/start.py backend call directly
            if titlelist:
                lines_count = len([x for x in titlelist.strip().split("\n") if x.strip()])
                result = f"Fix refs started for {lines_count} title(s)"
            elif number:
                result = f"Fix refs started for {number} pages"
            if test:
                result = f"[TEST] {result}"

    return render_template(
        "fixref.html",
        titlelist=titlelist,
        number=number,
        test=test,
        result=result,
    )


__all__ = ["bp_fixref"]
