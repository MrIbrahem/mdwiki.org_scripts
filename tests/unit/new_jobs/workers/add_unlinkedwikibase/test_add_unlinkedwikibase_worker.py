"""Unit tests for flask_app/main_app/new_jobs/workers/add_unlinkedwikibase/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask_app.main_app.new_jobs.workers.add_unlinkedwikibase.worker import (
    AddUnlinkedWikibaseWorker,
    add_unlinkedwikibase_worker_entry,
)


class TestAddUnlinkedWikibaseWorker:
    def test_get_job_type(self):
        worker = AddUnlinkedWikibaseWorker(job_id=1, args={}, user=None)
        assert worker.get_job_type() == "add_unlinkedwikibase"

    def test_result_object_is_shared_worker_object(self):
        from flask_app.main_app.new_jobs.shared_objects import SharedworkerObject
        worker = AddUnlinkedWikibaseWorker(job_id=1, args={}, user=None)
        assert isinstance(worker.result_object, SharedworkerObject)

    def test_process_sets_completed(self):
        worker = AddUnlinkedWikibaseWorker(job_id=1, args={}, user=None)
        result = worker.process()
        assert result.status == "completed"

    def test_args_stored(self):
        worker = AddUnlinkedWikibaseWorker(job_id=1, args={"key": "val"}, user=None)
        assert worker.args == {"key": "val"}
