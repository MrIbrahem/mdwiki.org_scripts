""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_redirect = Blueprint("main", __name__, url_prefix="/redirect")
logger = logging.getLogger(__name__)


@bp_redirect.route("/", methods=["GET"])
def redirect():
    return render_template(
        "redirect.html",
    )


__all__ = ["bp_redirect"]
