"""Blueprint for `/dup/` — fix duplicate redirects on mdwiki."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...jobs import runner
from ...jobs.store import get_store
from ...public_jobs_workers import fix_duplicate as svc
from ...su_services.users_service import current_user, oauth_required

bp_dup = Blueprint("dup", __name__, url_prefix="/dup")
logger = logging.getLogger(__name__)


@bp_dup.route("/", methods=["POST"])
@oauth_required
def dup_post():
    user = current_user()

    if request.form.get("start") != "start":
        return render_template("dup.html", title="Fix duplicate redirects")

    # Reject duplicate concurrent runs of this same tool.
    active = get_store().find_active("dup")
    if active is not None:
        flash(f"A duplicate-redirect job is already running ({active.id}).", "info")
        return redirect(url_for("jobs.status", job_id=active.id))

    job = runner.submit(
        "dup",
        svc.run,
        submitted_by=user.username,
        params={"save": True},
        save=True,
    )
    flash(f"Started fix-duplicate job {job.id}", "success")
    logger.info("dup job %s submitted by %s", job.id, user.username)
    return redirect(url_for("jobs.status", job_id=job.id))


@bp_dup.route("/", methods=["GET"])
def dup():
    return render_template("dup.html", title="Fix duplicate redirects")


__all__ = ["bp_dup"]
