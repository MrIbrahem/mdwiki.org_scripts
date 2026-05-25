"""Blueprint for `/fixred/` — fix redirects in page text."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...auth import current_user
from ...auth.decorators import login_required
from ...jobs import runner
from ...jobs.store import get_store
from ...services import fixred as svc

bp_fixred = Blueprint("fixred", __name__, url_prefix="/fixred")
logger = logging.getLogger(__name__)


def _normalize_title(raw: str) -> str:
    return (raw or "").replace("_", " ").strip()


@bp_fixred.route("/", methods=["GET"])
@login_required
def index():
    title = _normalize_title(request.args.get("title", ""))
    return render_template("fixred.html", title="Fix redirects in page text", form_title=title)


@bp_fixred.route("/all", methods=["POST"])
@login_required
def fixred_post_all():
    user = current_user()

    active = get_store().find_active("fixred")
    if active is not None:
        flash(f"A fixred job is already running ({active.id}).", "info")
        return redirect(url_for("jobs.status", job_id=active.id))

    job = runner.submit(
        "fixred",
        svc.run_all,
        submitted_by=user.username,
        params={"title": "all", "save": True},
        save=False,
    )

    flash(f"Started fixred job {job.id} for all pages", "success")
    logger.info("fixred job %s submitted by %s for all pages", job.id, user.username)
    return redirect(url_for("jobs.status", job_id=job.id))


@bp_fixred.route("/", methods=["POST"])
@login_required
def fixred_post():
    user = current_user()
    title = _normalize_title(request.form.get("title", ""))
    save = int(request.form.get("save", "0")) or 0

    if not title:
        flash("Please provide a title (use 'all' to process every mainspace page).", "warning")
        return redirect(url_for("fixred.index"))

    job = runner.submit(
        "fixred",
        svc.run,
        submitted_by=user.username,
        params={"title": title, "save": save},
        title=title,
        save=save,
    )

    flash(f"Started fixred job {job.id} for {title!r}", "success")
    logger.info("fixred job %s submitted by %s for title=%s", job.id, user.username, title)

    return redirect(url_for("jobs.status", job_id=job.id))


__all__ = ["bp_fixred"]
