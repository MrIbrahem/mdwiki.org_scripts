"""Blueprint for `/newupdater/` — synchronous medical-content updater."""

from __future__ import annotations

import logging
from urllib.parse import unquote

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ...shared import newupdater_service as svc
from ..auth.utils import oauth_required

# from ..utils.routes_utils import can_run_jobs

bp_newupdater = Blueprint("newupdater", __name__, url_prefix="/newupdater")

logger = logging.getLogger(__name__)


def _parse_title(title: str) -> str:
    title = title.replace("+", " ").replace("_", " ").strip()
    title = unquote(title)
    title = title.rstrip("/")
    return title


def _newupdater(title: str, save: bool) -> str:
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


@bp_newupdater.route("/<path:title>", methods=["GET"])
@oauth_required
def worker(title: str) -> str:
    title = _parse_title(title)
    return _newupdater(title, False)


@bp_newupdater.route("/save/<path:title>", methods=["GET"])
@oauth_required
def auto_save(title: str) -> str:
    """
    Process a title string and trigger a new update with auto-save enabled.
    NOTE: this route already used in https://mdwiki.org/wiki/MediaWiki:Sidebars:
        `**https://mdw.toolforge.org/newupdater/save/{{urlencode:{{PAGENAME}}}}|Med updater`

    Args:
        title (str): The raw title string to be processed.

    Returns:
        str: The result returned by the `_newupdater` function after processing the title.
    """
    title = _parse_title(title)
    return _newupdater(title, True)


@bp_newupdater.route("/update", methods=["GET"])
@oauth_required
def newupdater() -> str:
    title = _parse_title(request.args.get("title") or "")
    save = request.args.get("save") == "1"

    # If the title is empty, just render the default page without redirecting
    if not title:
        return _newupdater("", False)

    if save:
        # Redirect to auto_save route: /save/<path:title>
        return redirect(url_for("newupdater.auto_save", title=title))
    else:
        # Redirect to worker route: /<path:title>
        return redirect(url_for("newupdater.worker", title=title))


@bp_newupdater.route("/", methods=["GET"])
def index() -> str:
    return render_template(
        "newupdater.html",
        title="Medical content updater",
        form_title="",
        outcome=None,
        save=False,
    )


__all__ = [
    "bp_newupdater",
]
