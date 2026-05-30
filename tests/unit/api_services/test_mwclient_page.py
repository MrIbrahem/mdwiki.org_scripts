"""Unit tests for flask_app/main_app/api_services/mwclient_page.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from flask_app.main_app.api_services.mwclient_page import MwClientPage, _RETRY_DELAYS


class TestMwClientPageInit:
    def test_init(self):
        mock_site = MagicMock()
        page = MwClientPage("Test", mock_site)
        assert page.title == "Test"
        assert page.site is mock_site
        assert page.page is None
        assert page.load_page_error == ""


class TestRetryDelays:
    def test_is_tuple(self):
        assert isinstance(_RETRY_DELAYS, tuple)

    def test_has_delays(self):
        assert len(_RETRY_DELAYS) > 0

    def test_all_positive(self):
        for d in _RETRY_DELAYS:
            assert d > 0


class TestMwClientPageLoadPage:
    def test_returns_page_on_success(self):
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        page = MwClientPage("Test", mock_site)
        result = page.load_page()
        assert result is mock_page
        assert page.page is mock_page

    def test_caches_page(self):
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        page = MwClientPage("Test", mock_site)
        page.load_page()
        page.load_page()
        mock_site.pages.__getitem__.assert_called_once()


class TestMwClientPageCheckExists:
    def test_exists_returns_true(self):
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = True
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        page = MwClientPage("Test", mock_site)
        assert page.check_exists() is True

    def test_not_exists_returns_false(self):
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = False
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        page = MwClientPage("Test", mock_site)
        assert page.check_exists() is False


class TestMwClientPageEditPage:
    def test_load_failure_returns_error(self):
        mock_site = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(side_effect=Exception("fail"))
        page = MwClientPage("Test", mock_site)
        result = page.edit_page("text", "summary")
        assert result["success"] is False

    def test_success_returns_dict(self):
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.edit.return_value = {"newrevid": 123}
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        page = MwClientPage("Test", mock_site)
        result = page.edit_page("text", "summary")
        assert result["success"] is True
