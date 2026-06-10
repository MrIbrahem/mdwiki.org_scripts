"""Unit tests for src/main_app/jobs_workers/public_jobs_workers/add_r_column/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.add_r_column.worker import (
    AddRColumnWorker,
    add_to_tables,
    get_titles_redirects,
)


def test_add_to_tables_no_tables():
    text = "Plain text"
    assert add_to_tables(text, {}, []) == text


def test_add_to_tables_with_table():
    text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
    # add_to_tables should add R column because it's missing
    result = add_to_tables(text, {}, [])
    assert "! Header\n! R" in result


def test_get_titles_redirects():
    site = MagicMock()
    site.get.return_value = {
        "query": {
            "redirects": [
                {"from": "A", "to": "B"},
                {"from": "C", "to": "D"},
            ]
        }
    }
    titles = ["A", "C", "E"]
    result = get_titles_redirects(titles, site)
    assert result == {"A": "B", "C": "D"}
    site.get.assert_called_once()


class TestAddRColumnWorker:
    @pytest.fixture
    def worker(self):
        return AddRColumnWorker(job_id=1, args={}, user={"username": "test_user"})

    @patch("src.main_app.jobs_workers.public_jobs_workers.add_r_column.worker.get_user_site")
    @patch("src.main_app.jobs_workers.public_jobs_workers.add_r_column.worker.MwClientPage")
    @patch("src.main_app.jobs_workers.public_jobs_workers.add_r_column.worker.get_template_pages")
    def test_process_success(self, mock_get_template_pages, mock_mw_client_page, mock_get_user_site, worker):
        mock_site = MagicMock()
        mock_get_user_site.return_value = mock_site

        mock_page_obj = MagicMock()
        mock_mw_client_page.return_value = mock_page_obj

        mock_mw_page = MagicMock()
        mock_page_obj.load_page.return_value = mock_mw_page
        mock_page_obj.check_exists.return_value = True
        mock_mw_page.text.return_value = (
            '== List ==\n{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Aspirin]]\n|}'
        )

        mock_get_template_pages.return_value = ["Aspirin"]

        # Mock site.get for get_titles_redirects inside _newtext_step
        mock_site.get.return_value = {"query": {"redirects": []}}

        mock_page_obj.edit_page.return_value = {"success": True, "newrevid": 123}

        result = worker.process()

        assert result.status == "completed"
        assert result.steps.load_page.status == "completed"
        assert result.steps.final_save.status == "completed"
        assert result.steps.final_save.newrevid == 123

    @patch("src.main_app.jobs_workers.public_jobs_workers.add_r_column.worker.get_user_site")
    def test_process_no_site(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = None
        # When no site, BaseObjectsJobWorker.log_no_site_error sets status to failed
        result = worker.process()
        assert result.status == "failed"
