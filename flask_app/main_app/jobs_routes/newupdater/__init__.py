"""Blueprint for `/newupdater/` — synchronous medical-content updater."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, render_template, request

from ...public_jobs_workers import newupdater as svc
from ...su_services.users_service import oauth_required

bp_newupdater = Blueprint("newupdater", __name__, url_prefix="/newupdater")
logger = logging.getLogger(__name__)


@bp_newupdater.route("/", methods=["GET"])
@oauth_required
def newupdater():
    title = (request.args.get("title") or "").replace("_", " ").strip()
    save = int(request.args.get("save", "0")) or 0

    if not title:
        return render_template(
            "newupdater.html",
            title="Medical content updater",
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
            "newupdater.html",
            title="Medical content updater",
            form_title=title,
            outcome=None,
            save=save,
        )

    return render_template(
        "newupdater.html",
        title=f"Medical content updater — {title}",
        form_title=title,
        outcome=outcome,
        save=save,
    )


__all__ = ["bp_newupdater"]
