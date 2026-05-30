"""Unit tests for flask_app/main_app/shared/fixref_shared/make_title_bot.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask_app.main_app.shared.fixref_shared.make_title_bot import make_title


class TestMakeTitle:
    def setup_method(self):
        import flask_app.main_app.shared.fixref_shared.make_title_bot as mod

        mod.Title_cash.clear()

    def test_empty_url_returns_empty(self):
        assert make_title("") == {}
        assert make_title("   ") == ""

    @patch("flask_app.main_app.shared.fixref_shared.make_title_bot.get_url")
    def test_valid_response_returns_title(self, mock_get_url):
        mock_get_url.return_value = [{"title": "Aspirin"}]
        result = make_title("https://example.com/article")
        assert result == "Aspirin"

    @patch("flask_app.main_app.shared.fixref_shared.make_title_bot.get_url")
    def test_empty_response_returns_empty(self, mock_get_url):
        mock_get_url.return_value = {}
        result = make_title("https://example.com/empty")
        assert result == ""

    @patch("flask_app.main_app.shared.fixref_shared.make_title_bot.get_url")
    def test_not_found_title_returns_empty(self, mock_get_url):
        mock_get_url.return_value = [{"title": "Not found."}]
        result = make_title("https://example.com/404")
        assert result == ""

    @patch("flask_app.main_app.shared.fixref_shared.make_title_bot.get_url")
    def test_caching(self, mock_get_url):
        mock_get_url.return_value = [{"title": "Cached Title"}]
        result1 = make_title("https://example.com/cached")
        result2 = make_title("https://example.com/cached")
        assert result1 == "Cached Title"
        assert result2 == "Cached Title"
        assert mock_get_url.call_count == 1
