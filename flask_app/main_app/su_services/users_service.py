"""User authentication service — bridges OAuth callbacks to the DB layer."""

from __future__ import annotations

import logging
from typing import Optional

from ..db.services import get_authenticated_user_token, get_user_token, upsert_user_token
from .current_user import CurrentUser

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def save_and_get_user(
        user_id: int,
        username: str,
        access_key: str,
        access_secret: str,
    ) -> Optional[CurrentUser]:
        """Upsert OAuth credentials and return a CurrentUser composite."""
        try:
            upsert_user_token(
                user_id=user_id,
                username=username,
                access_key=access_key,
                access_secret=access_secret,
            )
            token = get_user_token(user_id)
            if not token:
                return None
            return CurrentUser(
                user_id=user_id,
                username=username,
                access_token=token.access_token,
                access_secret=token.access_secret,
            )
        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

    @staticmethod
    def get_authenticated_user(user_id: int) -> Optional[CurrentUser]:
        """Fetch the CurrentUser composite for session restoration."""
        try:
            token = get_authenticated_user_token(user_id)
            if not token:
                return None
            return CurrentUser(
                user_id=user_id,
                username=token.user.username,
                access_token=token.access_token,
                access_secret=token.access_secret,
            )
        except Exception as e:
            logger.error("Error loading user for ID %s: %s", user_id, e)
            return None


__all__ = [
    "UserService",
]
