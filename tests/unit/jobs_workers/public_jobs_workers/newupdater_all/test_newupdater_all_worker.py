"""Unit tests for src/main_app/public_jobs/workers/newupdater_all/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker import NewUpdaterAllWorker


class TestNewUpdaterAllWorker:
    def test_get_job_type(self):
        worker = NewUpdaterAllWorker(job_id=1, args={}, user=None)
        assert worker.get_job_type() == "newupdater_all"

    def test_result_type(self):
        from src.main_app.jobs_workers.shared_objects import SharedworkerObject

        worker = NewUpdaterAllWorker(job_id=1, args={}, user=None)
        assert isinstance(worker.result, SharedworkerObject)

    def test_make_new_text(self):
        worker = NewUpdaterAllWorker(job_id=1, args={}, user=None)
        with patch("src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker.med_updater_one", return_value="updated_text") as mock_med, \
             patch("src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker.add_param_named", return_value="final_text") as mock_add:
            new_text, summary = worker.make_new_text("Title", "original_text")
            assert new_text == "final_text"
            assert summary == "Med updater."
            mock_med.assert_called_once_with("Title", "original_text")
            mock_add.assert_called_once_with("updated_text")

    def test_process_success(self):
        with patch("src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker.get_user_site") as mock_get_site, \
             patch("src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker.get_category_members") as mock_get_members, \
             patch("src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker.MwClientPage") as mock_page_cls, \
             patch("src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker.med_updater_one") as mock_med_updater, \
             patch("src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker.add_param_named") as mock_add_param:
            
            mock_get_site.return_value = MagicMock()
            mock_get_members.return_value = ["Page1"]
            
            mock_page = MagicMock()
            mock_page.exists.return_value = True
            mock_page.get_text.return_value = "original text"
            mock_page.edit.return_value = {"success": True, "newrevid": 123}
            mock_page_cls.return_value = mock_page
            
            mock_med_updater.return_value = "new text"
            mock_add_param.return_value = "new text"
            
            worker = NewUpdaterAllWorker(job_id=1, args={}, user={"name": "test"})
            worker._save_progress = MagicMock()
            
            result = worker.process()
            assert result.summary.total == 1
            assert len(result.pages_changed) == 1
            assert result.pages_changed[0]["title"] == "Page1"
            assert result.pages_changed[0]["newrevid"] == 123
