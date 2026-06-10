""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    send_from_directory,
)

from ...jobs_workers.public_jobs_workers.workers_list_public import (
    jobs_data_for_all_pages,
    jobs_data_one_page,
)

bp_main = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

@bp_main.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        jobs_data_for_all_pages=jobs_data_for_all_pages,
        jobs_data_one_page=jobs_data_one_page,
    )


@bp_main.get("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico", mimetype="image/x-icon")


__all__ = ["bp_main"]
