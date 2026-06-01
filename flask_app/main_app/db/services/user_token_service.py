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


# ── SELECT ───────────────────────────────────────────────


def get_authenticated_user_token(user_id: int) -> None | UserTokenRecord:
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


def get_user_token(user_id: str | int) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user."""
    if not user_id:
        return None

    user_id = int(user_id)
    return db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()


def get_user_token_by_username(username: str) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user by username.

    Joins through the ``users`` table since username lives there.
    """
    username = (username or "").strip()
    if not username:
        return None

    return db.session.query(UserTokenRecord).join(UsersRecord).filter(UsersRecord.username == username).first()


# ── INSERT, UPDATE, SET ──────────────────────────────────


def create_user_token(user_id: int, access_key: str, access_secret: str) -> UserTokenRecord:
    """
    """
    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)

    orm_obj = UserTokenRecord(
        user_id=user_id,
        access_token=encrypted_token,
        access_secret=encrypted_secret,
    )
    db.session.add(orm_obj)

    db.session.commit()
    db.session.refresh(orm_obj)

    return orm_obj

def update_user_token(user_id: int, access_key: str, access_secret: str) -> UserTokenRecord:
    """
    Upsert the encrypted OAuth credentials for a user.
    Creates a new token row if one does not exist.
    """
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

        db.session.commit()
        db.session.refresh(orm_obj)
    return orm_obj

def upsert_user_token(user_id: int, access_key: str, access_secret: str) -> UserTokenRecord:
    """
    Upsert the encrypted OAuth credentials for a user.
    Creates a new token row if one does not exist.
    """

    # record = db.session.get(UserTokenRecord, user_id)
    record = db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()
    if record:
        orm_obj = update_user_token(user_id, access_key, access_secret)
    else:
        orm_obj = create_user_token(user_id, access_key, access_secret)

    return orm_obj


# ── DELETE ───────────────────────────────────────────────


def delete_user_token(user_id: int) -> bool:
    """Delete the stored OAuth token only. User identity row persists."""
    if not user_id:
        return False

    affected_rows = (
        db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).delete(synchronize_session=False)
    )
    db.session.commit()
    return affected_rows > 0


__all__ = [
    "upsert_user_token",
    "delete_user_token",
    "get_user_token",
    "get_user_token_by_username",
    "update_user_token",
]
