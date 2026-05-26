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
# /redirect/
# ---------------------------------------------------------------------------


class TestRedirect:
    def test_get_renders_form(self, mock_client, login):
        login("Doc James")
        r = mock_client.get("/redirect/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
        assert b'name="titlelist"' in r.data

    def test_post_single_title_submits_job(self, mock_client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import redirect as redsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(redsvc, "run", stub)
        login("Doc James")
        r = mock_client.post(
            "/redirect/",
            data={"title": "Aspirin", "csrf_token": csrf_token("/redirect/")},
        )
        assert r.status_code == 302
        _wait_done(mock_client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["titles"] == ["Aspirin"]

    def test_post_titlelist_dedupes_and_strips(self, mock_client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import redirect as redsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(redsvc, "run", stub)
        login("Doc James")
        r = mock_client.post(
            "/redirect/",
            data={
                "titlelist": "A\nB\n\n  A  \nC\n",
                "csrf_token": csrf_token("/redirect/"),
            },
        )
        assert r.status_code == 302
        _wait_done(mock_client, r.headers["Location"].rsplit("/", 1)[-1])
        # A appears twice in the input; deduped to once. Empties dropped.
        assert captured["titles"] == ["A", "B", "C"]

    def test_post_empty_re_renders_with_flash(self, mock_client, login, csrf_token):
        login("Doc James")
        r = mock_client.post(
            "/redirect/",
            data={"csrf_token": csrf_token("/redirect/")},
        )
        assert r.status_code == 200
        assert b"Provide at least one title" in r.data
