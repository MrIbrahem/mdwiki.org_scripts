from __future__ import annotations

from flask_app.main_app.api_services.clients.commons_client import create_commons_session


def test_create_commons_session():
    session = create_commons_session()
    assert session.headers["User-Agent"] == "SVGTranslateBot/1.0"


def test_create_commons_session_custom_ua():
    session = create_commons_session("CustomUA/2.0")
    assert session.headers["User-Agent"] == "CustomUA/2.0"
