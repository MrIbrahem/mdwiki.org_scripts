"""Unit tests for src/main_app/public_jobs/base_worker.py (test_base_worker.py)."""

from __future__ import annotations

import pytest

from src.main_app.jobs_workers.base_worker_object import BaseObjectsJobWorker


class TestBaseObjectsJobWorkerAbstract:
    def test_cannot_instantiate_without_methods(self):
        with pytest.raises(TypeError):
            BaseObjectsJobWorker(job_id=1)
