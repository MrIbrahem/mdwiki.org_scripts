"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

bp_fixred = Blueprint("main", __name__, url_prefix="/fixred")
logger = logging.getLogger(__name__)


@bp_fixred.route("/", methods=["GET"])
def fixred():
    title = request.values.get("title", "")
    test = request.values.get("test", "")

    result = None
    if title:
        logger.info(f"fixred triggered for title: {title}")
        # TODO: integrate fixred.py backend call directly
        result = f"Fix redirects job started for: {title}"
        if test:
            result = f"[TEST] {result}"

    return render_template(
        "fixred.html",
        title=title,
        test=test,
        result=result,
    )


__all__ = ["bp_fixred"]
