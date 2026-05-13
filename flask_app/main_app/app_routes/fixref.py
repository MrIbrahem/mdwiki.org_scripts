""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_fixref = Blueprint("main", __name__, url_prefix="/fixref")
logger = logging.getLogger(__name__)


@bp_fixref.route("/", methods=["GET"])
def fixref():
    return render_template(
        "fixref.html",
    )


__all__ = ["bp_fixref"]
