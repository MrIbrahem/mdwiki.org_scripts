"""Blueprint for `/import-history/` — import enwiki history (allow-list only)."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...auth import current_user
from ...auth.decorators import authorized_only, login_required
from ...jobs import runner
from ...jobs.store import get_store
from ...services import imp as svc

bp_import_history = Blueprint("import_history", __name__, url_prefix="/import-history")
logger = logging.getLogger(__name__)

# Mirrors plan §4.4 cap.
MAX_IMPORT_TITLES = 500


def _split_titles(raw_title: str, raw_titlelist: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    candidates: list[str] = []
    if raw_title:
        candidates.append(raw_title)
    if raw_titlelist:
        candidates.extend(raw_titlelist.splitlines())
    for c in candidates:
        t = c.replace("_", " ").strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


@bp_import_history.route("/", methods=["GET"])
@login_required
@authorized_only
def import_history():
    return render_template(
        "import-history.html",
        title="Import history from enwiki",
        form_title="",
        form_titlelist="",
        form_from="en",
    )


@bp_import_history.route("/", methods=["POST"])
@login_required
@authorized_only
def import_history_post():
    user = current_user()

    raw_title = request.form.get("title", "")
    raw_titlelist = request.form.get("titlelist", "")
    raw_from = (request.form.get("from", "") or "en").strip() or "en"

    titles = _split_titles(raw_title, raw_titlelist)
    if not titles:
        flash("Provide at least one title.", "warning")
        return render_template(
            "import-history.html",
            title="Import history from enwiki",
            form_title=raw_title,
            form_titlelist=raw_titlelist,
            form_from=raw_from,
        )
    if len(titles) > MAX_IMPORT_TITLES:
        flash(
            f"Too many titles ({len(titles)}); cap is {MAX_IMPORT_TITLES}.",
            "warning",
        )
        return render_template(
            "import-history.html",
            title="Import history from enwiki",
            form_title=raw_title,
            form_titlelist=raw_titlelist,
            form_from=raw_from,
        )

    active = get_store().find_active("import_history")
    if active is not None:
        flash(f"An import-history job is already running ({active.id}).", "info")
        return redirect(url_for("jobs.status", job_id=active.id))

    job = runner.submit(
        "import_history",
        svc.run,
        submitted_by=user.username,
        params={"title_count": len(titles), "from_lang": raw_from, "save": True},
        titles=titles,
        from_lang=raw_from,
        save=True,
    )
    flash(f"Started import-history job {job.id} for {len(titles)} title(s)", "success")
    logger.info(
        "import_history job %s submitted by %s for %d titles (from=%s)",
        job.id,
        user.username,
        len(titles),
        raw_from,
    )
    return redirect(url_for("jobs.status", job_id=job.id))


__all__ = ["bp_import_history"]
