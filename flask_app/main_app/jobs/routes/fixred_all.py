"""Blueprint for `/fixred_all/` — fix redirects in page text."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...su_services.users_service import current_user, oauth_required
from .. import runner
from ..store import get_store
from ..workers import fixred_all as svc

bp_fixred_all = Blueprint("fixred_all", __name__, url_prefix="/fixred_all")
logger = logging.getLogger(__name__)


def _normalize_title(raw: str) -> str:
    return (raw or "").replace("_", " ").strip()


@bp_fixred_all.route("/", methods=["GET"])
@oauth_required
def index():
    title = _normalize_title(request.args.get("title", ""))
    save = int(request.args.get("save", "0")) or 0
    return render_template(
        "jobs_templates/fixred_all.html",
        title="Fix redirects in all pages",
        form_title=title,
        outcome=None,
        save=save,
    )


@bp_fixred_all.route("/all", methods=["POST"])
@oauth_required
def fixred_post_all():
    user = current_user()

    active = get_store().find_active("fixred_all")
    if active is not None:
        flash(f"A fixred_all job is already running ({active.id}).", "info")
        return redirect(url_for("jobs.status", job_id=active.id))

    job = runner.submit(
        "fixred_all",
        svc.run_all,
        submitted_by=user.username,
        params={"title": "all", "save": True},
        save=False,
    )

    flash(f"Started fixred_all job {job.id} for all pages", "success")
    logger.info("fixred_all job %s submitted by %s for all pages", job.id, user.username)
    return redirect(url_for("jobs.status", job_id=job.id))


__all__ = ["bp_fixred_all"]
