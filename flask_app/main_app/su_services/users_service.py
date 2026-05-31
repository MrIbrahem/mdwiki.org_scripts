"""Helpers for loading the current authenticated user."""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional, TypeVar

from flask import g, request, session

from ..app_routes.auth.cookie import extract_user_id
from ..config import settings
from ..db.models import UserTokenRecord
from ..db.services import get_user_token

FuncType = TypeVar("FuncType", bound=Callable[..., Any])
logger = logging.getLogger(__name__)

def _resolve_user_id() -> int | None:
    uid = session.get("uid")
    if isinstance(uid, int):
        return uid
    try:
        return int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return None


def current_user() -> Optional[UserTokenRecord]:
    if hasattr(g, "_current_user"):
        return g._current_user  # type: ignore[attr-defined]

    user_id = _resolve_user_id()
    if user_id is None:
        signed = request.cookies.get(settings.cookie.name)
        if signed:
            user_id = extract_user_id(signed)
            if user_id is not None:
                session["uid"] = user_id
    try:
        user = get_user_token(user_id) if user_id is not None else None
    except Exception as e:
        logger.error("Error loading user token: %s", e)
        user = None

    if user and session.get("username") != user.username:
        session["username"] = user.username

    g._current_user = user  # type: ignore[attr-defined]
    return user

__all__ = [
    "current_user",
]
