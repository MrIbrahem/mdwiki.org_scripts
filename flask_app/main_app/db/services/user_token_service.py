"""
SQLAlchemy-based service for managing users and user tokens.

Users table is the stable identity layer. Tokens are a child of users.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from ...core.crypto import encrypt_value
from ...extensions import db
from ..models import UsersRecord, UserTokenRecord

logger = logging.getLogger(__name__)


def get_authenticated_user_token(user_id: int):
    """Fetch the CurrentUser composite for session restoration."""
    try:
        token = (
            db.session.query(UserTokenRecord)
            .options(joinedload(UserTokenRecord.user))
            .filter(UserTokenRecord.user_id == user_id)
            .first()
        )
        if not token or not token.user:
            return None
        return token
    except Exception as e:
        logger.error("Error loading user for ID %s: %s", user_id, e)
        return None


# ── User CRUD ───────────────────────────────────────────────


def create_user(user_id: int, username: str) -> UsersRecord:
    """Create a user identity row. Idempotent — returns existing if present."""
    existing = db.session.query(UsersRecord).filter(UsersRecord.user_id == user_id).first()
    if existing:
        if existing.username != username:
            existing.username = username
            try:
                db.session.commit()
                db.session.refresh(existing)
            except Exception:
                db.session.rollback()
                raise
        return existing

    record = UsersRecord(user_id=user_id, username=username)
    db.session.add(record)
    try:
        db.session.commit()
        db.session.refresh(record)
    except Exception:
        db.session.rollback()
        raise
    return record


def get_user(user_id: int) -> Optional[UsersRecord]:
    """Fetch a user by user_id."""
    if not user_id:
        return None
    return db.session.query(UsersRecord).filter(UsersRecord.user_id == int(user_id)).first()


def get_user_by_username(username: str) -> Optional[UsersRecord]:
    """Fetch a user by username."""
    username = (username or "").strip()
    if not username:
        return None
    return db.session.query(UsersRecord).filter(UsersRecord.username == username).first()


def delete_user(user_id: int) -> bool:
    """Delete user row. Cascades to user_tokens and admin_users via FK."""
    if not user_id:
        return False
    affected = db.session.query(UsersRecord).filter(UsersRecord.user_id == user_id).delete()
    db.session.commit()
    return affected > 0


def list_users() -> list[UsersRecord]:
    """Return all user identity records."""
    return db.session.query(UsersRecord).all()


# ── Token CRUD ──────────────────────────────────────────────


def upsert_user_token(*, user_id: int, username: str, access_key: str, access_secret: str) -> None:
    """Insert or update the encrypted OAuth credentials for a user.

    Automatically creates the ``users`` row if it does not exist.
    """
    username = (username or "").strip()

    # Ensure user identity row exists
    create_user(user_id, username)

    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)
    now = func.current_timestamp()

    orm_obj = db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()
    if orm_obj:
        orm_obj.access_token = encrypted_token
        orm_obj.access_secret = encrypted_secret
        orm_obj.updated_at = now
        orm_obj.last_used_at = now
        orm_obj.rotated_at = now
    else:
        orm_obj = UserTokenRecord(
            user_id=user_id,
            access_token=encrypted_token,
            access_secret=encrypted_secret,
            created_at=now,
            updated_at=now,
            last_used_at=now,
            rotated_at=None,
        )
        db.session.add(orm_obj)

    db.session.commit()


def get_user_token(user_id: str | int) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user."""
    if not user_id:
        return None

    user_id = int(user_id)
    return db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()


def delete_user_token(user_id: int) -> bool:
    """Delete the stored OAuth token only. User identity row persists."""
    if not user_id:
        return False

    affected_rows = (
        db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).delete(synchronize_session=False)
    )
    db.session.commit()
    return affected_rows > 0


def get_user_token_by_username(username: str) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user by username.

    Joins through the ``users`` table since username lives there.
    """
    username = (username or "").strip()
    if not username:
        return None

    # return db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user.user_id).first()
    return db.session.query(UserTokenRecord).join(UsersRecord).filter(UsersRecord.username == username).first()


__all__ = [
    "create_user",
    "delete_user",
    "delete_user_token",
    "get_user",
    "get_user_by_username",
    "get_user_token",
    "get_user_token_by_username",
    "list_users",
    "upsert_user_token",
]
