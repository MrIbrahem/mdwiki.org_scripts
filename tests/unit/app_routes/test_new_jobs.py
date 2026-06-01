"""Unit tests for flask_app/main_app/app_routes/new_jobs.py module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask_app.main_app.app_routes.new_jobs import _can_manage_job


class TestCanManageJob:
    def test_no_user(self):
        job = MagicMock()
        assert _can_manage_job(job, None) is False

    def test_admin_user(self):
        job = MagicMock()
        job.username = "someone"
        user = MagicMock()
        user.username = "admin_user"
        user.is_active_admin = True
        assert _can_manage_job(job, user) is True

    def test_job_owner(self):
        job = MagicMock()
        job.username = "owner"
        user = MagicMock()
        user.username = "owner"
        user.is_active_admin = False
        assert _can_manage_job(job, user) is True

    def test_non_owner_non_admin(self):
        job = MagicMock()
        job.username = "someone_else"
        user = MagicMock()
        user.username = "regular_user"
        user.is_active_admin = False
        assert _can_manage_job(job, user) is False

    def test_job_with_no_username(self):
        job = MagicMock()
        job.username = None
        user = MagicMock()
        user.username = "user"
        user.is_active_admin = False
        assert _can_manage_job(job, user) is False


@pytest.mark.usefixtures("app")
class TestNewJobsRoutes:
    def test_jobs_list_requires_valid_type(self, mock_client):
        resp = mock_client.get("/new_jobs/invalid_type")
        assert resp.status_code == 404

    def test_all_jobs_list_page(self, mock_client):
        resp = mock_client.get("/new_jobs/list")
        assert resp.status_code == 200
