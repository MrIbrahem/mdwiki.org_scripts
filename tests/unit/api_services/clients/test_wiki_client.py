from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask_app.main_app.api_services.clients.wiki_client import (
    coerce_encrypted,
    get_user_site,
)


def test_coerce_encrypted():
    assert coerce_encrypted(b"bytes") == b"bytes"
    assert coerce_encrypted(bytearray(b"array")) == b"array"
    assert coerce_encrypted(memoryview(b"view")) == b"view"
    assert coerce_encrypted("string") == b"string"
    assert coerce_encrypted(None) is None
    assert coerce_encrypted(123) is None


@patch("flask_app.main_app.api_services.clients.wiki_client.settings")
@patch("flask_app.main_app.api_services.clients.wiki_client.mwclient.Site")
@patch("flask_app.main_app.api_services.clients.wiki_client.decrypt_value")
def test_get_user_site(mock_decrypt, mock_site, mock_settings, app):
    mock_settings.oauth = MagicMock()
    mock_settings.other = MagicMock()
    mock_decrypt.side_effect = lambda x: x.decode() if isinstance(x, bytes) else x

    user = {"access_token": b"token", "access_secret": b"secret"}

    site = get_user_site(user)
    assert site is not None
    mock_site.assert_called_once()


def test_get_user_site_no_user():
    assert get_user_site(None) is None


def test_get_user_site_no_tokens():
    assert get_user_site({}) is None
