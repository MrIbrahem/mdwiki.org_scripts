from __future__ import annotations

import logging

from flask import Blueprint, flash, render_template

from ..db.services import get_user_jobs_stats
from ..su_services import current_user

logger = logging.getLogger(__name__)

bp_profile = Blueprint("profile", __name__, url_prefix="/profile")


@bp_profile.route("/", methods=["GET"])
def dashboard():
    user = current_user()
    if not user:
        flash("You must be logged in to view your profile.", "warning")
        return render_template("profile.html")

    data = get_user_jobs_stats(user.username)

    return render_template(
        "profile.html",
        username=user.username,
        stats=data["stats"],
        recent_jobs=data["recent_jobs"],
    )


@bp_profile.route("/<string:user_name>", methods=["GET"])
def user_dashboard(user_name: str):
    data = get_user_jobs_stats(user_name)

    return render_template(
        "profile.html",
        username=user_name,
        stats=data["stats"],
        recent_jobs=data["recent_jobs"],
    )


__all__ = ["bp_profile"]
