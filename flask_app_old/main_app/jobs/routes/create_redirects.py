"""Blueprint for `/create_redirects/` — copy enwiki redirects to mdwiki."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...su_services.users_service import current_user, oauth_required
from .. import runner
from ..store import get_store
from ..workers import create_redirects as svc

bp_redirect = Blueprint("create_redirects", __name__, url_prefix="/create_redirects")
logger = logging.getLogger(__name__)

# Cap input size so a runaway paste can't queue a million-page job.
_MAX_TITLES = 500


def _split_titles(raw_title: str, raw_titlelist: str) -> list[str]:
    """Combine the single-title field and the textarea into a deduped list."""

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


@bp_redirect.route("/", methods=["GET"], endpoint="create_redirects")
@oauth_required
def redirect_view():
    return render_template(
        "jobs_templates/create_redirects.html",
        title="Copy redirects from enwiki",
        form_title="",
        form_titlelist="",
    )


@bp_redirect.route("/", methods=["POST"], endpoint="redirect_post")
@oauth_required
def redirect_post():
    user = current_user()

    raw_title = request.form.get("title", "")
    raw_titlelist = request.form.get("titlelist", "")

    titles = _split_titles(raw_title, raw_titlelist)
    if not titles:
        flash("Provide at least one title.", "warning")
        return render_template(
            "jobs_templates/create_redirects.html",
            title="Copy redirects from enwiki",
            form_title=raw_title,
            form_titlelist=raw_titlelist,
        )
    if len(titles) > _MAX_TITLES:
        flash(f"Too many titles ({len(titles)}); cap is {_MAX_TITLES}.", "warning")
        return render_template(
            "jobs_templates/create_redirects.html",
            title="Copy redirects from enwiki",
            form_title=raw_title,
            form_titlelist=raw_titlelist,
        )

    active = get_store().find_active("create_redirects")
    if active is not None:
        flash(f"A create_redirects job is already running ({active.id}).", "info")
        return redirect(url_for("jobs.status", job_id=active.id))

    job = runner.submit(
        "create_redirects",
        svc.run,
        submitted_by=user.username,
        params={"title_count": len(titles), "save": True},
        titles=titles,
        save=True,
    )
    flash(f"Started create_redirects job {job.id} for {len(titles)} title(s)", "success")
    logger.info("create_redirects job %s submitted by %s for %d titles", job.id, user.username, len(titles))
    return redirect(url_for("jobs.status", job_id=job.id))


__all__ = ["bp_redirect"]
