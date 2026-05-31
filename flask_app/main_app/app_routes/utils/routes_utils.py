#
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from flask import g, url_for

from ...db.models import UserTokenRecord
from ...db.services.admin_service import active_coordinators
from ...new_jobs.workers_list import jobs_data

logger = logging.getLogger(__name__)


def context_user(wiki_domain: str, static_server: str) -> dict[str, Any]:
    """
    Used in @app.context_processor to inject variables into templates.
    """
    # Safe retrieval from g with a fallback to None
    user = getattr(g, "_current_user", None)

    username = user.username if user else None

    return {
        "current_user": user,
        "is_authenticated": user is not None,
        "username": username,
        "is_admin": bool(user and user.username in active_coordinators()),
        "wiki_domain": wiki_domain,
        "static_server": static_server,
    }


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


__all__ = [
    "context_user",
    "load_auth_payload",
    "get_job_detail_url",
]
