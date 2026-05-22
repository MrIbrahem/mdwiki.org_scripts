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


@bp_fixred.route("/", methods=["GET", "POST"])
@login_required
def fixred():
    user = current_user()

    # Read the title from POST first (form path), then fall back to GET (legacy
    # bookmark URLs like /fixred/?title=Aspirin still work).
    title = _normalize_title(request.values.get("title", ""))

    submitted = (request.method == "POST") or bool(request.args.get("title"))

    if submitted and title:
        active = get_store().find_active("fixred")
        if active is not None:
            flash(f"A fixred job is already running ({active.id}).", "info")
            return redirect(url_for("jobs.status", job_id=active.id))

        job = runner.submit(
            "fixred",
            svc.run,
            submitted_by=user.username,
            params={"title": title, "save": True},
            title=title,
            save=True,
        )
        flash(f"Started fixred job {job.id} for {title!r}", "success")
        logger.info("fixred job %s submitted by %s for title=%s", job.id, user.username, title)
        return redirect(url_for("jobs.status", job_id=job.id))

    if submitted and not title:
        flash("Please provide a title (use 'all' to process every mainspace page).", "warning")

    return render_template("fixred.html", title="Fix redirects in page text", form_title=title)


__all__ = ["bp_fixred"]
