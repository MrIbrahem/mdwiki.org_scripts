"""
"""

from __future__ import annotations

import logging

from ..exceptions import UserNotFoundError

from ...extensions import db
from ..models import UsersPermissionsRecord

logger = logging.getLogger(__name__)


def toggle_can_run_jobs(up_id: int, value: bool) -> UsersPermissionsRecord:
    """Toggle can_run_jobs."""
    record = db.session.query(UsersPermissionsRecord).filter(UsersPermissionsRecord.up_id == up_id).first()

    if not record:
        raise UserNotFoundError("User permissions record not found")

    record.can_run_jobs = value
    db.session.commit()
    db.session.refresh(record)
    return record

def toggle_can_run_bg_jobs(up_id: int, value: bool) -> UsersPermissionsRecord:
    """Toggle can_run_bg_jobs."""
    record = db.session.query(UsersPermissionsRecord).filter(UsersPermissionsRecord.up_id == up_id).first()

    if not record:
        raise UserNotFoundError("User permissions record not found")

    record.can_run_bg_jobs = value
    db.session.commit()
    db.session.refresh(record)
    return record


__all__ = [
]
