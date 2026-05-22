"""Blueprint for `/redirect/` — copy enwiki redirects to mdwiki."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...auth import current_user
from ...auth.decorators import login_required
from ...jobs import runner
from ...jobs.store import get_store
from ...services import redirect as svc

bp_redirect = Blueprint("redirect", __name__, url_prefix="/redirect")
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


@bp_redirect.route("/", methods=["GET", "POST"], endpoint="redirect")
@login_required
def redirect_view():
    user = current_user()

    raw_title = request.values.get("title", "")
    raw_titlelist = request.values.get("titlelist", "")

    if request.method == "POST":
        titles = _split_titles(raw_title, raw_titlelist)
        if not titles:
            flash("Provide at least one title.", "warning")
            return render_template(
                "redirect.html",
                title="Copy redirects from enwiki",
                form_title=raw_title,
                form_titlelist=raw_titlelist,
            )
        if len(titles) > _MAX_TITLES:
            flash(f"Too many titles ({len(titles)}); cap is {_MAX_TITLES}.", "warning")
            return render_template(
                "redirect.html",
                title="Copy redirects from enwiki",
                form_title=raw_title,
                form_titlelist=raw_titlelist,
            )

        active = get_store().find_active("redirect")
        if active is not None:
            flash(f"A redirect job is already running ({active.id}).", "info")
            return redirect(url_for("jobs.status", job_id=active.id))

        job = runner.submit(
            "redirect",
            svc.run,
            submitted_by=user.username,
            params={"title_count": len(titles), "save": True},
            titles=titles,
            save=True,
        )
        flash(f"Started redirect job {job.id} for {len(titles)} title(s)", "success")
        logger.info(
            "redirect job %s submitted by %s for %d titles", job.id, user.username, len(titles)
        )
        return redirect(url_for("jobs.status", job_id=job.id))

    return render_template(
        "redirect.html",
        title="Copy redirects from enwiki",
        form_title=raw_title,
        form_titlelist=raw_titlelist,
    )


__all__ = ["bp_redirect"]
