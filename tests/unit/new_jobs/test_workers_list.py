"""Unit tests for flask_app/main_app/new_jobs/workers_list.py module."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from flask_app.main_app.new_jobs.workers_list import JobData, jobs_data


class TestJobData:
    def test_create_job_data(self):
        jd = JobData(
            job_type="test",
            job_name="Test Job",
            job_callable=lambda: None,
            job_list_template="test/list.html",
        )
        assert jd.job_type == "test"
        assert jd.job_name == "Test Job"
        assert jd.job_list_template == "test/list.html"
        assert jd.job_details_template == "jobs_templates/_help_templates/shared_details.html"

    def test_custom_details_template(self):
        jd = JobData(
            job_type="test",
            job_name="Test",
            job_callable=lambda: None,
            job_list_template="list.html",
            job_details_template="custom/details.html",
        )
        assert jd.job_details_template == "custom/details.html"

    def test_default_details_template(self):
        jd = JobData(
            job_type="x",
            job_name="X",
            job_callable=lambda: None,
            job_list_template="x.html",
        )
        assert "shared_details" in jd.job_details_template


class TestJobsData:
    def test_jobs_data_is_dict(self):
        assert isinstance(jobs_data, dict)

    def test_expected_job_types_present(self):
        expected = {
            "add_r_column",
            "add_unlinkedwikibase",
            "create_redirects",
            "duplicate_redirect",
            "find_and_replace",
            "fixred_all",
            "fixref",
            "import_history",
        }
        assert set(jobs_data.keys()) == expected

    def test_all_values_are_job_data(self):
        for key, val in jobs_data.items():
            assert isinstance(val, JobData), f"jobs_data[{key!r}] is not JobData"

    def test_job_type_matches_key(self):
        for key, val in jobs_data.items():
            assert val.job_type == key, f"Mismatch: key={key!r}, job_type={val.job_type!r}"

    def test_all_have_callable(self):
        for key, val in jobs_data.items():
            assert callable(val.job_callable), f"jobs_data[{key!r}].job_callable not callable"

    def test_all_have_list_template(self):
        for key, val in jobs_data.items():
            assert val.job_list_template, f"jobs_data[{key!r}].job_list_template is empty"

    def test_all_have_non_empty_name(self):
        for key, val in jobs_data.items():
            assert val.job_name, f"jobs_data[{key!r}].job_name is empty"
