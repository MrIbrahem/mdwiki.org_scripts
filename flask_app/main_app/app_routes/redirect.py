"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

bp_redirect = Blueprint("main", __name__, url_prefix="/redirect")
logger = logging.getLogger(__name__)


@bp_redirect.route("/", methods=["GET", "POST"])
def redirect():
    test = request.values.get("test", "")
    title = request.values.get("title", "")
    titlelist = request.values.get("titlelist", "")

    result = None
    if request.method == "POST":
        if (title or titlelist):
            logger.info(f"redirect triggered: title={title}")
            # TODO: integrate red.py backend call directly
            if title:
                result = f"Redirect creation started for: {title}"
            elif titlelist:
                lines_count = len([x for x in titlelist.strip().split("\n") if x.strip()])
                result = f"Redirect creation started for {lines_count} title(s)"
            if test:
                result = f"[TEST] {result}"

    return render_template(
        "redirect.html",
        test=test,
        title=title,
        titlelist=titlelist,
        result=result,
    )


__all__ = ["bp_redirect"]
