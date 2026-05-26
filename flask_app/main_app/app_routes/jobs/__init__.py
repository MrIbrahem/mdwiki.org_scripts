"""Generic job status pages: HTML view, JSON poller, cooperative stop."""

from __future__ import annotations

import logging

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, url_for

from ...jobs.store import get_store
from ...su_services.users_service import oauth_required

bp_jobs = Blueprint("jobs", __name__, url_prefix="/jobs")
logger = logging.getLogger(__name__)


@bp_jobs.get("/list")
def jobs_list() -> str:
    jobs = get_store().all()
    return render_template("jobs/list.html", jobs=jobs)


@bp_jobs.get("/<job_id>")
def status(job_id: str):
    job = get_store().get(job_id)
    if job is None:
        abort(404)
    return render_template("jobs/status.html", job=job, title=f"Job {job_id}")


@bp_jobs.get("/<job_id>.json")
def status_json(job_id: str):
    job = get_store().get(job_id)
    if job is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(job.to_dict())


@bp_jobs.post("/<job_id>/stop")
@oauth_required
def stop(job_id: str):
    """Cooperatively stop a running job by setting its stop_event.

    The service decides where in its loop to actually break out — see plan
    §10 (stop signal) and the per-service ``stop_event`` handling.
    """

    job = get_store().get(job_id)
    if job is None:
        abort(404)
    if job.status in ("done", "error"):
        flash(f"Job {job_id} already finished ({job.status}); nothing to stop.", "info")
        return redirect(url_for("jobs.status", job_id=job_id))

    job.stop_event.set()
    job.log.append("stop requested by user")
    flash(f"Stop signal sent to job {job_id}.", "warning")
    logger.info("stop signal sent to job %s", job_id)
    return redirect(url_for("jobs.status", job_id=job_id))


__all__ = ["bp_jobs"]
