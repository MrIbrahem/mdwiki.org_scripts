"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

bp_newupdater = Blueprint("main", __name__, url_prefix="/newupdater")
logger = logging.getLogger(__name__)


@bp_newupdater.route("/", methods=["GET"])
def newupdater():
    test = request.values.get("test", "")
    title = request.values.get("title", "")
    save = request.values.get("save", "")
    save_checked = "checked" if save else ""

    result = None
    if title:
        logger.info(f"newupdater triggered for title: {title}, save={bool(save)}")
        # TODO: integrate newupdater/med.py backend call directly
        result = f"Med updater started for: {title}"
        if save:
            result += " (auto-save enabled)"
        if test:
            result = f"[TEST] {result}"

    return render_template(
        "newupdater.html",
        test=test,
        title=title,
        save=save,
        save_checked=save_checked,
        result=result,
    )


__all__ = ["bp_newupdater"]
