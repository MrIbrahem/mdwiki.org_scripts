""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_dup = Blueprint("main", __name__, url_prefix="/dup")
logger = logging.getLogger(__name__)


@bp_dup.route("/", methods=["GET"])
def dup():
    return render_template(
        "dup.html",
    )


__all__ = ["bp_dup"]
