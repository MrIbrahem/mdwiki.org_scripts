"""Shared pytest fixtures.

Boot a Flask app once per session with CSRF on (so tests exercise the
real protection path) and provide helpers for scraping CSRF tokens and
for switching session identity. Each test gets a fresh JobStore so jobs
don't leak across tests.
"""

from __future__ import annotations

import os
import re
import secrets
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from pytest_socket import disable_socket

# Make the flask_app/ directory importable as `main_app`. The repo's prod
# entrypoint flask_app/app.py does the same trick.
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "flask_app"))

# ── Set ALL env vars before any src.* import ─────────────────────────────────
# config.py executes get_settings() at module level and raises RuntimeError
# if FLASK_SECRET_KEY is missing, so every env var must be set here first,
# before any import that pulls in src.main_app.
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("OAUTH_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
os.environ.setdefault("OAUTH_CONSUMER_KEY", "test-consumer-key")
os.environ.setdefault("OAUTH_CONSUMER_SECRET", "test-consumer-secret")
os.environ.setdefault("OAUTH_MWURI", "https://example.org/w/index.php")

# Pin allowlist for tests so we don't depend on the prod default drifting.
os.environ.setdefault("ALLOWLIST_USERS", "Doc James,Mr. Ibrahem")


@pytest.fixture(autouse=True)
def stop_nets():
    disable_socket(allow_unix_socket=True)


@pytest.fixture(scope="session")
def app():
    """Create the Flask app once per test session."""

    from flask_app.main_app import create_app
    from flask_app.main_app.config import TestingConfig

    application = create_app(TestingConfig)
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def mock_client(app):
    """Fresh test client per test."""

    return app.test_client()


@pytest.fixture(autouse=True)
def reset_job_store():
    """Reset the in-memory JobStore between tests."""

    from flask_app.main_app.jobs import store as store_mod

    store_mod._store = None
    yield
    store_mod._store = None


@pytest.fixture()
def login(mock_client):
    """Helper to set ``session['username']`` to a given user."""

    def _login(username: str) -> None:
        with mock_client.session_transaction() as session:
            session["username"] = username

    return _login


@pytest.fixture()
def csrf_token(mock_client):
    """Scrape a CSRF token out of any page that contains a form."""

    pattern = re.compile(r'name="csrf_token" value="([^"]+)"')

    def _csrf(path: str = "/") -> str:
        body = mock_client.get(path).data.decode()
        match = pattern.search(body)
        if not match:
            raise AssertionError(f"no csrf_token found in body for {path!r}")
        return match.group(1)

    return _csrf


@pytest.fixture()
def stub_service(monkeypatch):
    """Replace ``services.<tool>.run`` with a deterministic stub.

    The stub captures the kwargs it was called with on a list, then drives
    the runner's ``on_progress`` once and returns a small result dict.
    """

    captured: dict[str, list[dict]] = {}

    def _make(name: str, *, raises: BaseException | None = None):
        captured.setdefault(name, [])

        def stub(*, on_progress, stop_event, **kwargs):
            captured[name].append(kwargs)
            if raises is not None:
                raise raises
            on_progress(0, 2, f"{name} starting")
            on_progress(2, 2, f"{name} done")
            return {"tool": name, "kwargs": _summarize(kwargs)}

        return stub, captured[name]

    return _make


def _summarize(kwargs: dict) -> dict:
    """Reduce list-valued kwargs to lengths for compact assertions."""

    out: dict = {}
    for key, value in kwargs.items():
        if isinstance(value, list):
            out[f"{key}_len"] = len(value)
        else:
            out[key] = value
    return out
