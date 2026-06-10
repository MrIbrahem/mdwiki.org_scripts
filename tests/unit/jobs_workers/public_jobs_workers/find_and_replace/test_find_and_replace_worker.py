"""Unit tests for src/main_app/jobs_workers/public_jobs_workers/find_and_replace/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.find_and_replace.worker import (
    FindAndReplaceWorker,
)


class TestFindAndReplaceWorker:
    @pytest.fixture
    def worker(self):
        return FindAndReplaceWorker(
            job_id=1,
            args={"str_find": "findme", "str_replace": "replaceme", "listtype": "newlist"},
            user={"username": "test_user"},
        )

    @patch("src.main_app.jobs_workers.public_jobs_workers.find_and_replace.worker.get_user_site")
    @patch("src.main_app.jobs_workers.public_jobs_workers.find_and_replace.worker.MwClientPage")
    def test_process_success(self, mock_mw_client_page, mock_get_user_site, worker):
        mock_site = MagicMock()
        mock_get_user_site.return_value = mock_site

        mock_site.search.return_value = [{"title": "Page 1"}]

        mock_page = MagicMock()
        mock_mw_client_page.return_value = mock_page
        mock_page.exists.return_value = True
        mock_page.get_text.return_value = "This is a findme text."

        mock_page.edit.return_value = {"success": True, "newrevid": 789}

        result = worker.process()

        assert result.status == "completed"
        assert len(result.pages_changed) == 1
        assert result.pages_changed[0]["title"] == "Page 1"
        assert result.pages_changed[0]["newrevid"] == 789

    @patch("src.main_app.jobs_workers.public_jobs_workers.find_and_replace.worker.get_user_site")
    def test_process_no_site(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = None
        result = worker.process()
        assert result.status == "failed"

    @patch("src.main_app.jobs_workers.public_jobs_workers.find_and_replace.worker.get_user_site")
    def test_process_missing_str_find(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = MagicMock()
        worker.args["str_find"] = ""
        result = worker.process()
        assert result.status == "failed"
        assert result.error == "`find` cannot be empty."
