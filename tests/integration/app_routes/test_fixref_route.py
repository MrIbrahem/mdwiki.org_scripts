""" """

from __future__ import annotations

import time

from flask_app.main_app.jobs.store import get_store


def _wait_done(mock_client, job_id, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = mock_client.get(f"/jobs/{job_id}.json").get_json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(0.005)
    return data


# ---------------------------------------------------------------------------
# /fixref/
# ---------------------------------------------------------------------------


class TestFixref:
    def test_get_renders_form(self, mock_client, login):
        login("Doc James")
        r = mock_client.get("/fixref/")
        assert r.status_code == 200
        assert b'name="titlelist"' in r.data
        assert b'name="cat"' in r.data
        assert b'name="number"' in r.data

    def test_post_titlelist_submits_job(self, mock_client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import fixref as fsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(fsvc, "run", stub)
        login("Doc James")
        r = mock_client.post(
            "/fixref/",
            data={"titlelist": "A\nB", "csrf_token": csrf_token("/fixref/")},
        )
        assert r.status_code == 302
        _wait_done(mock_client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["titles"] == ["A", "B"]
        assert captured["category"] is None
        assert captured["number"] is None

    def test_post_category_submits_job(self, mock_client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import fixref as fsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(fsvc, "run", stub)
        login("Doc James")
        r = mock_client.post(
            "/fixref/",
            data={"cat": "Drugs", "csrf_token": csrf_token("/fixref/")},
        )
        assert r.status_code == 302
        _wait_done(mock_client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["category"] == "Drugs"
        assert captured["titles"] in (None, [])

    def test_post_number_submits_job(self, mock_client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import fixref as fsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(fsvc, "run", stub)
        login("Doc James")
        r = mock_client.post(
            "/fixref/",
            data={"number": "50", "csrf_token": csrf_token("/fixref/")},
        )
        assert r.status_code == 302
        _wait_done(mock_client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["number"] == 50

    def test_post_all_empty_re_renders_with_flash(self, mock_client, login, csrf_token):
        login("Doc James")
        r = mock_client.post("/fixref/", data={"csrf_token": csrf_token("/fixref/")})
        assert r.status_code == 200
        assert b"Provide at least one of" in r.data
