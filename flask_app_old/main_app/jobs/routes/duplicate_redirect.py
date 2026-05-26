"""Blueprint for `/duplicate_redirect/` — fix duplicate redirects on mdwiki."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...su_services.users_service import current_user, oauth_required
from .. import runner
from ..store import get_store
from ..workers import fix_duplicate as svc

bp_dup = Blueprint("duplicate_redirect", __name__, url_prefix="/duplicate_redirect")
logger = logging.getLogger(__name__)


@bp_dup.route("/", methods=["POST"])
@oauth_required
def dup_post():
    user = current_user()

    if request.form.get("start") != "start":
        return render_template("jobs_templates/duplicate_redirect.html", title="Fix duplicate redirects")

    # Reject duplicate concurrent runs of this same tool.
    active = get_store().find_active("duplicate_redirect")
    if active is not None:
        flash(f"A duplicate-redirect job is already running ({active.id}).", "info")
        return redirect(url_for("jobs.status", job_id=active.id))

    job = runner.submit(
        "duplicate_redirect",
        svc.run,
        submitted_by=user.username,
        params={"save": True},
        save=True,
    )
    flash(f"Started fix-duplicate job {job.id}", "success")
    logger.info("duplicate_redirect job %s submitted by %s", job.id, user.username)
    return redirect(url_for("jobs.status", job_id=job.id))


@bp_dup.route("/", methods=["GET"])
def duplicate_redirect():
    return render_template("jobs_templates/duplicate_redirect.html", title="Fix duplicate redirects")


__all__ = ["bp_dup"]
