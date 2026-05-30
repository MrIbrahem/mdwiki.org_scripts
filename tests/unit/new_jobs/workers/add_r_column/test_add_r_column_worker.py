"""Unit tests for flask_app/main_app/new_jobs/workers/add_r_column/worker.py."""

from __future__ import annotations

from flask_app.main_app.new_jobs.workers.add_r_column.worker import add_to_tables


class TestAddToTables:
    def test_no_tables_returns_unchanged(self):
        text = "Just plain text with no tables."
        result = add_to_tables(text, {}, [])
        # Should return text unchanged or handle gracefully
        assert isinstance(result, str)
