"""Blueprint for `/find_and_replace/` — find-and-replace bot (allow-list only)."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...su_services.users_service import current_user, oauth_required
from .. import runner
from ..store import get_store
from ..workers import find_and_replace as svc

bp_replace = Blueprint("find_and_replace", __name__, url_prefix="/find_and_replace")
logger = logging.getLogger(__name__)


def _parse_int(raw: str) -> int | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    return max(0, n) or None


@bp_replace.route("/", methods=["GET"])
@oauth_required
def replace():
    return render_template(
        "jobs_templates/find_and_replace.html",
        title="Find and replace",
        form_find="",
        form_replace="",
        form_number="",
        form_listtype="newlist",
    )


@bp_replace.route("/", methods=["POST"])
@oauth_required
def replace_post():
    user = current_user()

    raw_find = request.form.get("find", "")
    raw_replace = request.form.get("replace", "")
    raw_number = request.form.get("number", "")
    listtype = request.form.get("listtype", "newlist")
    if listtype not in ("newlist", "oldlist"):
        listtype = "newlist"

    if not raw_find:
        flash("`find` cannot be empty.", "warning")
        return render_template(
            "jobs_templates/find_and_replace.html",
            title="Find and replace",
            form_find=raw_find,
            form_replace=raw_replace,
            form_number=raw_number,
            form_listtype=listtype,
        )

    active = get_store().find_active("find_and_replace")
    if active is not None:
        flash(f"A find_and_replace job is already running ({active.id}).", "info")
        return redirect(url_for("jobs.status", job_id=active.id))

    number = _parse_int(raw_number)

    params = {
        "listtype": listtype,
        "number": number,
        "find_len": len(raw_find),
        "replace_len": len(raw_replace),
        "save": True,
    }

    job = runner.submit(
        "find_and_replace",
        svc.run,
        submitted_by=user.username,
        params=params,
        find=raw_find,
        replace=raw_replace,
        listtype=listtype,
        number=number,
        save=True,
    )
    flash(f"Started find_and_replace job {job.id} (listtype={listtype})", "success")
    logger.info(
        "find_and_replace job %s submitted by %s (listtype=%s, find_len=%d)",
        job.id,
        user.username,
        listtype,
        len(raw_find),
    )
    return redirect(url_for("jobs.status", job_id=job.id))


# Compatibility shim for legacy bookmarks of the form
# /replace-log.php?id=<job-id> — they used to land on the per-job log page.
@bp_replace.get("/log")
def replace_log_compat():
    job_id = request.args.get("id", "").strip()
    if not job_id:
        return redirect(url_for("find_and_replace.replace"))
    return redirect(url_for("jobs.status", job_id=job_id))


__all__ = ["bp_replace"]
