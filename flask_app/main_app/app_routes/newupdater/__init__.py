"""Blueprint for `/newupdater/` — synchronous medical-content updater."""

from __future__ import annotations

import difflib
import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...auth.decorators import login_required
from ...services import newupdater as svc

bp_newupdater = Blueprint("newupdater", __name__, url_prefix="/newupdater")
logger = logging.getLogger(__name__)


def _make_diff(title: str, old: str, new: str) -> str:
    """Return a unified diff string suitable for a ``<pre>`` block."""

    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"{title} (current)",
        tofile=f"{title} (proposed)",
        n=3,
    )
    return "".join(diff)


@bp_newupdater.route("/", methods=["GET"])
@login_required
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
            diff="",
        )

    try:
        outcome = svc.work_on_title(title)
    except Exception as exc:  # noqa: BLE001
        logger.exception("work_on_title failed for %s", title)
        flash(f"Error processing {title!r}: {exc!r}", "danger")
        return render_template(
            "newupdater.html",
            title="Medical content updater",
            form_title=title,
            outcome=None,
            save=save,
            diff="",
        )

    diff = _make_diff(title, outcome.old_text, outcome.new_text) if outcome.has_changes else ""
    return render_template(
        "newupdater.html",
        title=f"Medical content updater — {title}",
        form_title=title,
        outcome=outcome,
        save=save,
        diff=diff,
    )


@bp_newupdater.route("/", methods=["POST"])
@login_required
def newupdater_post():
    title = (request.form.get("title") or "").replace("_", " ").strip()
    save = int(request.form.get("save", "0")) or 0

    if not title:
        flash("Provide a title to save.", "warning")
        return redirect(url_for("newupdater.newupdater", save=save))
    try:
        ok, status = svc.save_page(title)
    except Exception as exc:  # noqa: BLE001
        logger.exception("save_page failed for %s", title)
        flash(f"Save failed: {exc!r}", "danger")
        return redirect(url_for("newupdater.newupdater", title=title, save=save))

    if ok:
        flash(f"Saved {title!r}.", "success")
    elif status == "no_changes":
        flash(f"{title!r}: no changes to save.", "info")
    elif status == "notext":
        flash(f"{title!r}: page is empty or rewriter produced no text.", "warning")
    else:
        flash(f"{title!r}: save failed ({status}).", "danger")
    return redirect(url_for("newupdater.newupdater", title=title, save=save))


__all__ = ["bp_newupdater"]
