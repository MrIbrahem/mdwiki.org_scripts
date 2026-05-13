"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

bp_import_history = Blueprint("main", __name__, url_prefix="/import-history")
logger = logging.getLogger(__name__)

AUTHORIZED_USERS = ["Doc James", "Mr. Ibrahem"]


@bp_import_history.route("/", methods=["GET", "POST"])
def import_history():
    test = request.values.get("test", "")
    from_ = request.values.get("from", "")
    title = request.values.get("title", "")
    titlelist = request.values.get("titlelist", "")

    result = None
    if request.method == "POST":
        if (title or titlelist):
            logger.info(f"import-history triggered: title={title}, from={from_}")
            # TODO: integrate imp.py backend call directly
            if title:
                result = f"Import history for {title}"
                if from_:
                    result += f" from {from_}"
            elif titlelist:
                lines_count = len([x for x in titlelist.strip().split("\n") if x.strip()])
                result = f"Import history for {lines_count} title(s)"
            if test:
                result = f"[TEST] {result}"

    return render_template(
        "import-history.html",
        test=test,
        from_=from_,
        title=title,
        titlelist=titlelist,
        result=result,
    )


__all__ = ["bp_import_history"]
