"""Auth decorators for blueprint endpoints."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import abort, flash, redirect, request, url_for

from .current_user import current_user, is_authorized


def login_required(view: Callable) -> Callable:
    """Bounce anonymous users back to the index with a flash message.

    Phase-1: there is no real login page, so we redirect to ``/`` and leave a
    flash. The contract is stable; the redirect target will become the OAuth
    flow once it lands.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user.is_authenticated:
            flash(f"You must be logged in to use {request.path}.", "warning")
            return redirect(url_for("main.index"))
        return view(*args, **kwargs)

    return wrapper


def authorized_only(view: Callable) -> Callable:
    """403 for users who are not on the configured allow-list."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not is_authorized(user):
            abort(403)
        return view(*args, **kwargs)

    return wrapper


__all__ = ["authorized_only", "login_required"]
