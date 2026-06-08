"""Unit tests for flask_app/main_app/public_jobs/workers/add_r_column/worker.py."""

from __future__ import annotations

from flask_app.main_app.jobs_workers.public_jobs_workers.add_r_column.worker import add_to_tables


class TestAddToTables:
    def test_no_tables_returns_unchanged(self):
        text = "Just plain text with no tables."
        result = add_to_tables(text, {}, [])
        # Should return text unchanged or handle gracefully
        assert result == "Just plain text with no tables."
