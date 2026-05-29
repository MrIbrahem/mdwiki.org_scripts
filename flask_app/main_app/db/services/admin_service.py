"""
SQLAlchemy-based service for managing coordinators.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func
from ...extensions import db
from ..models import AdminUserRecord

logger = logging.getLogger(__name__)

def active_coordinators() -> list[str]:
    """"""
    results = [
    ]
    return results


__all__ = [
    "active_coordinators",
]
