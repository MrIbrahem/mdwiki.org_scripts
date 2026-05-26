"""Blueprint for `/fixref/` — normalize references on a list/category/N pages."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...jobs import runner
from ...jobs.store import get_store
from ...public_jobs_workers import fixref as svc
from ...su_services.users_service import current_user, oauth_required

bp_fixref = Blueprint("fixref", __name__, url_prefix="/fixref")
logger = logging.getLogger(__name__)


def _split_titlelist(raw: str) -> list[str]:
    return [line.strip() for line in (raw or "").splitlines() if line.strip()]


def _parse_int(raw: str) -> int | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    return max(0, n) or None


@bp_fixref.route("/", methods=["GET"])
@oauth_required
def fixref():
    return render_template(
        "fixref.html",
        title="Normalize references",
        form_titlelist="",
        form_number="",
        form_cat="",
    )


@bp_fixref.route("/", methods=["POST"])
@oauth_required
def fixref_post():
    user = current_user()

    raw_titlelist = request.form.get("titlelist", "")
    raw_number = request.form.get("number", "")
    raw_cat = request.form.get("cat", "")
    titles = _split_titlelist(raw_titlelist)
    number = _parse_int(raw_number)
    category = (raw_cat or "").strip() or None

    if not (titles or number or category):
        flash(
            "Provide at least one of: a title list, a number of pages, or a category.",
            "warning",
        )
        return render_template(
            "fixref.html",
            title="Normalize references",
            form_titlelist=raw_titlelist,
            form_number=raw_number,
            form_cat=raw_cat,
        )

    active = get_store().find_active("fixref")
    if active is not None:
        flash(f"A fixref job is already running ({active.id}).", "info")
        return redirect(url_for("jobs.status", job_id=active.id))

    params: dict = {"save": True}
    if titles:
        params["title_count"] = len(titles)
    if category:
        params["category"] = category
    if number:
        params["number"] = number

    job = runner.submit(
        "fixref",
        svc.run,
        submitted_by=user.username,
        params=params,
        titles=titles or None,
        category=category,
        number=number,
        save=True,
    )
    flash(f"Started fixref job {job.id}", "success")
    logger.info(
        "fixref job %s submitted by %s (titles=%d, number=%s, cat=%s)",
        job.id,
        user.username,
        len(titles),
        number,
        category,
    )
    return redirect(url_for("jobs.status", job_id=job.id))


__all__ = ["bp_fixref"]
