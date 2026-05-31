"""Blueprint for `/newupdater/` — synchronous medical-content updater."""

from __future__ import annotations

import logging
import urllib.parse

from flask import Blueprint, flash, g, render_template, request

from ...shared import newupdater_service as svc
from ..auth.utils import oauth_required

bp_newupdater = Blueprint("newupdater", __name__, url_prefix="/newupdater")

logger = logging.getLogger(__name__)

def _prase_title(title: str) -> str:
    title = title.replace("+", " ").replace("_", " ").strip()
    title = urllib.parse.unquote(title)
    return title

def _newupdater(title: str, save: int) -> str:
    if not title:
        return render_template(
            "newupdater.html",
            title="Medical content updater",
            form_title="",
            outcome=None,
            save=save,
        )

    user = getattr(g, "_current_user", None)

    try:
        outcome = svc.newupdater_one_title(
            title=title,
            save=save,
            summary="Med updater.",
            user=user,
        )
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

@bp_newupdater.route("/", methods=["GET"])
@oauth_required
def newupdater() -> str:
    title = _prase_title(request.args.get("title") or "")
    save = int(request.args.get("save", "0")) or 0
    return _newupdater(title, save)


@bp_newupdater.route("/<path:title>", methods=["GET"])
@oauth_required
def worker(title: str) -> str:
    title = _prase_title(title)
    title = urllib.parse.unquote(title)
    return _newupdater(title, False)


@bp_newupdater.route("/save/<path:title>", methods=["GET"])
@oauth_required
def auto_save(title: str) -> str:
    title = _prase_title(title)
    title = urllib.parse.unquote(title)
    return _newupdater(title, True)


@bp_newupdater.route("/", methods=["GET"])
def index() -> str:
    return render_template(
        "newupdater.html",
        title="Medical content updater",
        form_title="",
        outcome=None,
        save=False,
    )


__all__ = ["bp_newupdater"]
