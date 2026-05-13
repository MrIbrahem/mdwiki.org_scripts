"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_replace = Blueprint("main", __name__, url_prefix="/replace")
logger = logging.getLogger(__name__)


@bp_replace.route("/", methods=["GET"])
def replace():
    return render_template("replace.html", )


__all__ = ["bp_replace"]
