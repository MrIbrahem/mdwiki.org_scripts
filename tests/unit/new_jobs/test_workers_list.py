from __future__ import annotations

from flask_app.main_app.new_jobs.workers_list import (
    JOB_TYPE_TEMPLATES_PUBLIC,
    jobs_targets_public,
)


def test_workers_list_integrity():
    # Check that public jobs have both a target worker and a template
    for job_type in jobs_targets_public:
        assert job_type in JOB_TYPE_TEMPLATES_PUBLIC
        assert callable(jobs_targets_public[job_type])


def test_known_job_types():
    expected_types = {
        "add_r_column",
        "add_unlinkedwikibase",
        "create_redirects",
        "duplicate_redirect",
        "find_and_replace",
        "fixred_all",
        "fixref",
        "import_history",
    }
    assert set(jobs_targets_public.keys()) == expected_types
