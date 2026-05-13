""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_import_history = Blueprint("main", __name__, url_prefix="/import-history")
logger = logging.getLogger(__name__)


@bp_import_history.route("/", methods=["GET"])
def import_history():
    return render_template(
        "import-history.html",
    )


__all__ = ["bp_import_history"]
