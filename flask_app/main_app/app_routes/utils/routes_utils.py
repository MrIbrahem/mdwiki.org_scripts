#
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from flask import url_for

from ...db.models import UserTokenRecord
from ...new_jobs.workers_list import jobs_data

logger = logging.getLogger(__name__)


def load_auth_payload(user: Optional[UserTokenRecord] | None) -> Dict[str, Any]:
    auth_payload: Dict[str, Any] = {}
    if user:
        # returns (access_key, access_secret) and marks token used
        access_key, access_secret = user.access_token, user.access_secret

        auth_payload = {
            "id": user.user_id,
            "username": user.username,
            "access_token": access_key,
            "access_secret": access_secret,
        }
    return auth_payload


def get_job_detail_url(job_id: int, job_type: str) -> str:
    """Returns the correct job detail URL based on job type."""
    if job_type in jobs_data:
        return url_for("new_jobs.job_detail", job_type=job_type, job_id=job_id)
    return url_for("admin.jobs.job_detail", job_type=job_type, job_id=job_id)
