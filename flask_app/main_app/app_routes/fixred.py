""""""

from __future__ import annotations

import logging

from flask import Blueprint, flash, render_template, request

from ..su_services.users_service import oauth_required
from ..shared import fixred_one

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
        "fixred_one.html",
        title="Fix redirects in page text",
        form_title=title,
        outcome=None,
        save=save,
    )


@bp_fixred.route("/", methods=["POST"])
@oauth_required
def fixred_post():
    title = _normalize_title(request.form.get("title", ""))
    save = int(request.form.get("save", "0")) or 0

    if not title:
        return render_template(
            "fixred_one.html",
            title="Fix redirects in page text",
            form_title="",
            outcome=None,
            save=save,
        )

    try:
        outcome = fixred_one.work_on_title(title, save)
    except Exception as exc:
        logger.exception("work_on_title failed for %s", title)
        flash(f"Error processing {title!r}: {exc!r}", "danger")
        return render_template(
            "fixred_one.html",
            title="Fix redirects in page text",
            form_title=title,
            outcome=None,
            save=save,
        )

    return render_template(
        "fixred_one.html",
        title=f"Fix redirects in page text — {title}",
        form_title=title,
        outcome=outcome,
        save=save,
    )


__all__ = ["bp_fixred"]
