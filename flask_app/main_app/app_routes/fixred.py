""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_fixred = Blueprint("main", __name__, url_prefix="/fixred")
logger = logging.getLogger(__name__)


@bp_fixred.route("/", methods=["GET"])
def fixred():
    return render_template(
        "fixred.html",
    )


__all__ = ["bp_fixred"]
