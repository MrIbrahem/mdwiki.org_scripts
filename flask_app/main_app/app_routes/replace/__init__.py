"""Blueprint for `/replace/` — find-and-replace bot (allow-list only)."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...auth import current_user
from ...auth.decorators import authorized_only, login_required
from ...jobs import runner
from ...jobs.store import get_store
from ...services import replace as svc

bp_replace = Blueprint("replace", __name__, url_prefix="/replace")
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


@bp_replace.route("/", methods=["GET", "POST"])
@login_required
@authorized_only
def replace():
    user = current_user()

    raw_find = request.values.get("find", "")
    raw_replace = request.values.get("replace", "")
    raw_number = request.values.get("number", "")
    listtype = request.values.get("listtype", "newlist")
    if listtype not in ("newlist", "oldlist"):
        listtype = "newlist"

    if request.method == "POST":
        if not raw_find:
            flash("`find` cannot be empty.", "warning")
            return render_template(
                "replace.html",
                title="Find and replace",
                form_find=raw_find,
                form_replace=raw_replace,
                form_number=raw_number,
                form_listtype=listtype,
            )

        active = get_store().find_active("replace")
        if active is not None:
            flash(f"A replace job is already running ({active.id}).", "info")
            return redirect(url_for("jobs.status", job_id=active.id))

        number = _parse_int(raw_number)

        # Don't put the find/replace strings into job.params verbatim — the
        # runner exposes params on the status page, and these can be huge or
        # contain wikitext that breaks rendering. Store length only.
        params = {
            "listtype": listtype,
            "number": number,
            "find_len": len(raw_find),
            "replace_len": len(raw_replace),
            "save": True,
        }

        job = runner.submit(
            "replace",
            svc.run,
            submitted_by=user.username,
            params=params,
            find=raw_find,
            replace=raw_replace,
            listtype=listtype,
            number=number,
            save=True,
        )
        flash(f"Started replace job {job.id} (listtype={listtype})", "success")
        logger.info(
            "replace job %s submitted by %s (listtype=%s, find_len=%d)",
            job.id,
            user.username,
            listtype,
            len(raw_find),
        )
        return redirect(url_for("jobs.status", job_id=job.id))

    return render_template(
        "replace.html",
        title="Find and replace",
        form_find=raw_find,
        form_replace=raw_replace,
        form_number=raw_number,
        form_listtype=listtype,
    )


# Compatibility shim for legacy bookmarks of the form
# /replace-log.php?id=<job-id> — they used to land on the per-job log page.
@bp_replace.get("/log")
def replace_log_compat():
    job_id = request.args.get("id", "").strip()
    if not job_id:
        return redirect(url_for("replace.replace"))
    return redirect(url_for("jobs.status", job_id=job_id))


__all__ = ["bp_replace"]
