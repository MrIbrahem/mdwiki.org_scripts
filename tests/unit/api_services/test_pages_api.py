"""Unit tests for flask_app/main_app/api_services/pages_api.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask_app.main_app.api_services.pages_api import (
    create_page,
    get_page_text,
    import_page_from_wiki,
    is_page_exists,
    is_redirect,
    move_page,
    update_page_text,
)


class TestIsPageExists:
    def test_returns_bool(self):
        mock_site = MagicMock()
        with patch("flask_app.main_app.api_services.pages_api.MwClientPage") as MockPage:
            MockPage.return_value.check_exists.return_value = True
            assert is_page_exists("Test", mock_site) is True

    def test_returns_false_for_missing(self):
        mock_site = MagicMock()
        with patch("flask_app.main_app.api_services.pages_api.MwClientPage") as MockPage:
            MockPage.return_value.check_exists.return_value = False
            assert is_page_exists("Missing", mock_site) is False


class TestIsRedirect:
    def test_returns_bool(self):
        mock_site = MagicMock()
        with patch("flask_app.main_app.api_services.pages_api.MwClientPage") as MockPage:
            MockPage.return_value.is_redirect.return_value = True
            assert is_redirect("Redirect", mock_site) is True


class TestMovePage:
    def test_missing_fields_returns_error(self):
        result = move_page(None, "", "NewTitle")
        assert result["success"] is False
        assert "Missing" in result["error"]

    def test_valid_calls_mwclient(self):
        mock_site = MagicMock()
        with patch("flask_app.main_app.api_services.pages_api.MwClientPage") as MockPage:
            MockPage.return_value.move_page.return_value = {"success": True}
            result = move_page(mock_site, "Old", "New")
            assert result["success"] is True
            MockPage.assert_called_once_with("Old", mock_site)
            MockPage.return_value.move_page.assert_called_once_with("New", reason="", move_talk=True, no_redirect=False)


class TestCreatePage:
    def test_missing_fields_returns_error(self):
        result = create_page("", "", None)
        assert result["success"] is False
        assert "Missing" in result["error"]

    def test_valid_calls_edit(self):
        mock_site = MagicMock()
        with patch("flask_app.main_app.api_services.pages_api.MwClientPage") as MockPage:
            MockPage.return_value.create_page.return_value = {"success": True}
            result = create_page("Test", "content", mock_site)
            assert result["success"] is True
            MockPage.assert_called_once_with("Test", mock_site)
            MockPage.return_value.create_page.assert_called_once_with("content", "")


class TestUpdatePageText:
    def test_missing_fields_returns_error(self):
        result = update_page_text("", "", None)
        assert result["success"] is False


class TestGetPageText:
    def test_missing_fields_returns_empty(self):
        assert get_page_text("", None) == ""

    def test_returns_text(self):
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.text.return_value = "page content"
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        result = get_page_text("Test", mock_site)
        assert result == "page content"


class TestImportPageFromWiki:
    def test_returns_result(self):
        mock_site = MagicMock()
        mock_site.post.return_value = {"imported": True}
        result = import_page_from_wiki(mock_site, "Test")
        assert result == {"imported": True}
        mock_site.post.assert_called_once_with(
            action="import",
            title="Test",
            interwikisource="wikipedia",
            fullhistory=1,
        )

    def test_error_returns_dict(self):
        mock_site = MagicMock()
        mock_site.post.side_effect = Exception("fail")
        result = import_page_from_wiki(mock_site, "Test")
        assert "error" in result
