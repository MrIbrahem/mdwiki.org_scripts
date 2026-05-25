"""
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import (
    flash,
    redirect,
    url_for,
)

from ..su_services.users_service import current_user


def login_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that redirects anonymous users to the index page."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            flash("You must be logged in to view this page", "warning")
            return redirect(url_for("main.index"))
        return fn(*args, **kwargs)

    return wrapper


__all__ = [
    "login_required",
]
