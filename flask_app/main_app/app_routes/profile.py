from __future__ import annotations

import logging

from flask import Blueprint, render_template, flash
from sqlalchemy import func

from ..db.models.jobs import JobRecord
from ..extensions import db
from ..su_services.users_service import current_user

logger = logging.getLogger(__name__)

bp_profile = Blueprint("profile", __name__, url_prefix="/profile")


@bp_profile.route("/", methods=["GET"])
@bp_profile.route("/dashboard", methods=["GET"])
def dashboard():
    user = current_user()
    if not user:
        flash("You must be logged in to view your profile.", "warning")
        return render_template("profile.html")

    username = user.username

    base_query = db.session.query(JobRecord).filter(JobRecord.username == username)

    total_jobs = base_query.count()

    status_counts = dict(
        db.session.query(JobRecord.status, func.count(JobRecord.id))
        .filter(JobRecord.username == username)
        .group_by(JobRecord.status)
        .all()
    )

    type_counts = dict(
        db.session.query(JobRecord.job_type, func.count(JobRecord.id))
        .filter(JobRecord.username == username)
        .group_by(JobRecord.job_type)
        .all()
    )

    recent_jobs = (
        base_query.order_by(JobRecord.created_at.desc())
        .limit(50)
        .all()
    )

    stats = {
        "total": total_jobs,
        "completed": status_counts.get("completed", 0),
        "failed": status_counts.get("failed", 0),
        "running": status_counts.get("running", 0),
        "pending": status_counts.get("pending", 0),
        "cancelled": status_counts.get("cancelled", 0),
    }

    return render_template(
        "profile.html",
        username=username,
        stats=stats,
        type_counts=type_counts,
        recent_jobs=recent_jobs,
    )


__all__ = ["bp_profile"]
