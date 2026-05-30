"""
SQLAlchemy-based service for managing coordinators.

only active_coordinators need db_guard

"""

from __future__ import annotations

import logging
from typing import List

from ...extensions import db
from ..models import AdminUserRecord
from .utils import db_guard

logger = logging.getLogger(__name__)


@db_guard(default_return=[], msg="Failed to active coordinators")
def active_coordinators() -> list[str]:
    """Get a list of active coordinator usernames from the database."""
    records = db.session.query(AdminUserRecord).filter(AdminUserRecord.is_active).all()
    return [u.username for u in records]


def list_coordinators() -> List[AdminUserRecord]:
    """
    Return all coordinators from the database.

    Returns a list of records, or an empty list on failure.
    """
    return db.session.query(AdminUserRecord).all()


def get_coordinator_by_id(coordinator_id: int) -> AdminUserRecord:
    """
    Get a coordinator by ID.
    """
    record = db.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
    if not record:
        raise LookupError(f"Coordinator id {coordinator_id} was not found")
    return record


def add_coordinator(username: str) -> AdminUserRecord:
    """Add a coordinator."""

    if not username:
        raise ValueError("Username is required")

    record = db.session.query(AdminUserRecord).filter(AdminUserRecord.username == username).first()
    if record:
        # This assumes a UNIQUE constraint on the username column
        raise ValueError(f"Coordinator '{username}' already exists") from None

    record = AdminUserRecord(username=username, is_active=True)
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def set_coordinator_active(coordinator_id: int, is_active: bool) -> AdminUserRecord:
    """Toggle coordinator activity."""
    # record = get_coordinator_by_id(coordinator_id)
    record = db.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
    if record:
        record.is_active = is_active
        db.session.commit()
        db.session.refresh(record)
        return record


def delete_coordinator(coordinator_id: int) -> bool:
    """
    Delete a coordinator efficiently.

    Returns True if rows were affected, False otherwise (or on failure).
    """
    affected_rows = (
        db.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).delete(synchronize_session=False)
    )
    return affected_rows > 0


__all__ = [
    "get_coordinator_by_id",
    "list_coordinators",
    "active_coordinators",
    "add_coordinator",
    "set_coordinator_active",
    "delete_coordinator",
]
