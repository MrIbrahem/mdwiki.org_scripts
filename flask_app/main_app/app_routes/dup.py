"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

bp_dup = Blueprint("main", __name__, url_prefix="/dup")
logger = logging.getLogger(__name__)


@bp_dup.route("/", methods=["GET", "POST"])
def dup():
    test = request.values.get("test", "")
    start = request.values.get("start", "")

    result = None
    if request.method == "POST" and start:
        logger.info("fix_duplicate job triggered")
        # TODO: integrate fix_duplicate.py backend call directly
        result = "Fix duplicate job queued"
        if test:
            result = f"[TEST] {result}"

    return render_template(
        "dup.html",
        test=test,
        start=start,
        result=result,
    )


__all__ = ["bp_dup"]
