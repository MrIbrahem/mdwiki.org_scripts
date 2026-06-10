"""Unit tests for src/main_app/jobs_workers/public_jobs_workers/create_redirects/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.create_redirects.worker import (
    CreateRedirectsWorker,
    _valid_title,
)


def test_valid_title():
    assert _valid_title("Aspirin") is True
    assert _valid_title("Aspirin (disambiguation)") is False
    assert _valid_title("Category:Medical") is False
    assert _valid_title("Template:Medical") is False
    assert _valid_title("User:Test") is False


class TestCreateRedirectsWorker:
    @pytest.fixture
    def worker(self):
        return CreateRedirectsWorker(job_id=1, args={"titles": ["Aspirin"]}, user={"username": "test_user"})

    @patch("src.main_app.jobs_workers.public_jobs_workers.create_redirects.worker.get_user_site")
    @patch("src.main_app.jobs_workers.public_jobs_workers.create_redirects.worker.MwClientPage")
    @patch("src.main_app.jobs_workers.public_jobs_workers.create_redirects.worker.get_redirects_for")
    @patch("src.main_app.jobs_workers.public_jobs_workers.create_redirects.worker.is_pages_exists")
    def test_process_success(
        self, mock_is_pages_exists, mock_get_redirects_for, mock_mw_client_page, mock_get_user_site, worker
    ):
        mock_site = MagicMock()
        mock_get_user_site.return_value = mock_site

        # Mock target page
        mock_target_page = MagicMock()
        mock_mw_client_page.side_effect = lambda t, s: mock_target_page if t == "Aspirin" else MagicMock()
        mock_target_page.exists.return_value = True

        mock_get_redirects_for.return_value = ["Acetylsalicylic acid"]
        mock_is_pages_exists.return_value = {"Acetylsalicylic acid": False}

        # Mock redirect page creation
        mock_redirect_page = MagicMock()
        mock_mw_client_page.side_effect = lambda t, s: mock_target_page if t == "Aspirin" else mock_redirect_page
        mock_redirect_page.create.return_value = {"success": True}

        result = worker.process()

        assert result.status == "completed"
        assert result.summary.created == 1
        assert result.summary.scanned == 1

    @patch("src.main_app.jobs_workers.public_jobs_workers.create_redirects.worker.get_user_site")
    def test_process_no_site(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = None
        result = worker.process()
        assert result.status == "failed"
