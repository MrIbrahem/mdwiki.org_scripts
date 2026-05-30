"""Unit tests for flask_app/main_app/new_jobs/workers/add_r_column/add_rtt.py."""

from __future__ import annotations

from flask_app.main_app.new_jobs.workers.add_r_column.add_rtt import fix_title


class TestFixTitle:
    def test_removes_wikilinks(self):
        assert fix_title("[[Aspirin]]") == "Aspirin"

    def test_removes_html_entities(self):
        assert fix_title("&#039;test&#039;") == "'test'"

    def test_plain_title_unchanged(self):
        assert fix_title("Aspirin") == "Aspirin"

    def test_empty_string(self):
        assert fix_title("") == ""

    def test_wikilinks_with_entity(self):
        assert fix_title("[[It&#039;s a test]]") == "It's a test"
