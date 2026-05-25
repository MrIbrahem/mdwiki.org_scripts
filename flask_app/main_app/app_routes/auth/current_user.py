"""Session-backed `current_user()` with a localhost-only dev backdoor."""

from __future__ import annotations

from dataclasses import dataclass

from flask import has_request_context, request, session

from ...config import settings


@dataclass(frozen=True)
class User:
    """Minimal user model. The username is the MediaWiki user name."""

    username: str

    @property
    def is_authenticated(self) -> bool:
        return bool(self.username)


ANONYMOUS = User(username="")


def _localhost_dev_user() -> str:
    """When running on localhost, accept ?dev_user=Name and persist it.

    The check uses :func:`settings.is_localhost` against ``request.host`` so
    that this backdoor cannot be triggered by spoofed headers in production.
    """

    try:
        host = request.host or ""
    except RuntimeError:
        return ""
    if not settings.is_localhost(host):
        return ""
    candidate = (request.values.get("dev_user") or "").strip()
    if not candidate:
        return ""
    session["username"] = candidate
    return candidate


def current_user() -> User:
    """Return the authenticated user, or :data:`ANONYMOUS`.

    Outside a request context returns ANONYMOUS instead of raising — this lets
    job-runner threads call :func:`current_user` without special-casing.
    """

    if not has_request_context():
        return ANONYMOUS

    dev = _localhost_dev_user()
    username = dev or session.get("username", "")
    return User(username=username) if username else ANONYMOUS


def is_authorized(user: User) -> bool:
    """True iff `user` is authenticated and on the configured allow-list."""

    if not user.is_authenticated:
        return False
    return user.username in settings.allowlist_users


__all__ = ["ANONYMOUS", "User", "current_user", "is_authorized"]
