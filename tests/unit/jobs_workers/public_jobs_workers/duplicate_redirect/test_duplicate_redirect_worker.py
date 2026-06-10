"""Unit tests for src/main_app/jobs_workers/public_jobs_workers/duplicate_redirect/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.duplicate_redirect.worker import (
    DuplicateRedirectWorker,
    resolve_redirect_chains,
)


def test_resolve_redirect_chains():
    redirects = [
        {"from": "A", "to": "B"},
        {"from": "B", "to": "C"},
        {"from": "D", "to": "E"},
    ]
    # A -> B -> C (C is final target)
    # D -> E (E is final target)
    result = resolve_redirect_chains(redirects)

    # Sort results by title for consistent comparison
    result.sort(key=lambda x: x["title"])

    assert result == [
        {"title": "A", "redirect_to": "B", "final_target": "C"},
        {"title": "D", "redirect_to": "E", "final_target": "E"},
    ]


class TestDuplicateRedirectWorker:
    @pytest.fixture
    def worker(self):
        return DuplicateRedirectWorker(job_id=1, args={}, user={"username": "test_user"})

    @patch("src.main_app.jobs_workers.public_jobs_workers.duplicate_redirect.worker.get_user_site")
    @patch("src.main_app.jobs_workers.public_jobs_workers.duplicate_redirect.worker.get_double_redirects")
    @patch("src.main_app.jobs_workers.public_jobs_workers.duplicate_redirect.worker.MwClientPage")
    @patch("src.main_app.jobs_workers.public_jobs_workers.duplicate_redirect.worker.replace_wikilink_destinations")
    def test_process_success(self, mock_replace, mock_mw_client_page, mock_get_double, mock_get_user_site, worker):
        mock_site = MagicMock()
        mock_get_user_site.return_value = mock_site

        mock_get_double.return_value = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ]

        mock_page = MagicMock()
        mock_mw_client_page.return_value = mock_page
        mock_page.exists.return_value = True
        mock_page.get_text.return_value = "#REDIRECT [[B]]"

        mock_replace.return_value = "#REDIRECT [[C]]"
        mock_page.edit.return_value = {"success": True, "newrevid": 456}

        result = worker.process()

        assert result.status == "completed"
        assert len(result.pages_changed) == 1
        assert result.pages_changed[0]["from_title"] == "A"
        assert result.pages_changed[0]["newrevid"] == 456

    @patch("src.main_app.jobs_workers.public_jobs_workers.duplicate_redirect.worker.get_user_site")
    def test_process_no_site(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = None
        result = worker.process()
        assert result.status == "failed"
