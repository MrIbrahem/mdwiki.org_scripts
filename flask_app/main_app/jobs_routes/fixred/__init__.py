"""Blueprint for `/fixred/` — fix redirects in page text."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...jobs import runner
from ...jobs.store import get_store
from ...public_jobs_workers import fixred as svc
from ...su_services.users_service import current_user, oauth_required

bp_fixred = Blueprint("fixred", __name__, url_prefix="/fixred")
logger = logging.getLogger(__name__)


def _normalize_title(raw: str) -> str:
    return (raw or "").replace("_", " ").strip()


@bp_fixred.route("/", methods=["GET"])
@oauth_required
def index():
    title = _normalize_title(request.args.get("title", ""))
    save = int(request.args.get("save", "0")) or 0
    return render_template(
        "fixred.html",
        title="Fix redirects in page text",
        form_title=title,
        outcome=None,
        save=save,
    )


@bp_fixred.route("/all", methods=["POST"])
@oauth_required
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
@oauth_required
def fixred_post():
    title = _normalize_title(request.form.get("title", ""))
    save = int(request.form.get("save", "0")) or 0

    if not title:
        return render_template(
            "fixred.html",
            title="Fix redirects in page text",
            form_title="",
            outcome=None,
            save=save,
        )

    try:
        outcome = svc.work_on_title(title, save)
    except Exception as exc:
        logger.exception("work_on_title failed for %s", title)
        flash(f"Error processing {title!r}: {exc!r}", "danger")
        return render_template(
            "fixred.html",
            title="Fix redirects in page text",
            form_title=title,
            outcome=None,
            save=save,
        )

    return render_template(
        "fixred.html",
        title=f"Fix redirects in page text — {title}",
        form_title=title,
        outcome=outcome,
        save=save,
    )


__all__ = ["bp_fixred"]
