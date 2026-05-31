from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests
from flask_app.main_app.api_services.category import (
    get_category_members_api,
)


@patch("flask_app.main_app.api_services.category.requests.Session")
def test_get_category_members_api_success(mock_session_cls):
    mock_session = mock_session_cls.return_value
    mock_response = MagicMock()
    mock_response.json.side_effect = [
        {
            "query": {"categorymembers": [{"title": "Page 1"}, {"title": "Page 2"}]},
            "continue": {"cmcontinue": "cont123"},
        },
        {"query": {"categorymembers": [{"title": "Page 3"}]}},
    ]
    mock_session.get.return_value = mock_response

    members = get_category_members_api("Category:Test", "example.org")
    assert members == ["Page 1", "Page 2", "Page 3"]
    assert mock_session.get.call_count == 2


@patch("flask_app.main_app.api_services.category.requests.Session")
def test_get_category_members_api_error(mock_session_cls):
    mock_session = mock_session_cls.return_value
    mock_session.get.side_effect = requests.exceptions.RequestException("API Error")

    members = get_category_members_api("Category:Test", "example.org")
    assert members == []
