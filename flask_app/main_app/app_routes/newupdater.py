"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_newupdater = Blueprint("main", __name__, url_prefix="/newupdater")
logger = logging.getLogger(__name__)


@bp_newupdater.route("/", methods=["GET"])
def newupdater():
    return render_template("newupdater.html", )


__all__ = ["bp_newupdater"]
