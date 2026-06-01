"""User authentication service — bridges OAuth callbacks to the DB layer."""

from __future__ import annotations

import logging
from typing import Optional

from ..db.services import (
    create_user,
    get_authenticated_user_token,
    get_user_by_username,
    get_user_token,
    is_active_coordinator,
    upsert_user_token,
)
from ..db.services.users_service import UsersRecord
from .current_user import CurrentUser

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def save_and_get_user(
        username: str,
        access_key: str,
        access_secret: str,
    ) -> Optional[CurrentUser]:
        """Upsert OAuth credentials and return a CurrentUser composite."""
        try:
            username = (username or "").strip()

            # Ensure user identity row exists
            user: UsersRecord = get_user_by_username(username)

            if not user:
                user: UsersRecord = create_user(username)

            user_id = user.user_id

            # 1. Update or insert into database via repository
            upsert_user_token(
                user_id=user_id,
                access_key=access_key,
                access_secret=access_secret,
            )

            # 2. Get the fresh record
            token = get_user_token(user_id)
            if not token:
                return None

            return CurrentUser(
                user_id=user_id,
                username=username,
                access_token=token.access_token,
                access_secret=token.access_secret,
                can_run_jobs=user.can_run_jobs,
                can_run_bg_jobs=user.can_run_bg_jobs,
                is_active_admin=is_active_coordinator(username),
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
                can_run_jobs=token.user.can_run_jobs,
                can_run_bg_jobs=token.user.can_run_bg_jobs,
                is_active_admin=is_active_coordinator(token.user.username),
            )
        except Exception as e:
            logger.error("Error loading user for ID %s: %s", user_id, e)
            return None


__all__ = [
    "UserService",
]
