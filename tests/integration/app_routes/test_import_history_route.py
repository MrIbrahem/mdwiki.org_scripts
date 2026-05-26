""" """

from __future__ import annotations

import time


def _wait_done(mock_client, job_id, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = mock_client.get(f"/jobs/{job_id}.json").get_json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(0.005)
    return data


# ---------------------------------------------------------------------------
# /import-history/  — requires allowlist
# ---------------------------------------------------------------------------


class TestImportHistory:
    def test_unlisted_user_gets_403(self, mock_client, login):
        login("Plain User")
        r = mock_client.get("/import-history/")
        assert r.status_code == 403

    def test_allowlisted_get_renders_form(self, mock_client, login):
        login("Doc James")
        r = mock_client.get("/import-history/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
        assert b'name="titlelist"' in r.data

    def test_post_submits_job_with_titles_and_from(self, mock_client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import imp

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(imp, "run", stub)
        login("Doc James")
        r = mock_client.post(
            "/import-history/",
            data={
                "titlelist": "A\nB",
                "from": "en",
                "csrf_token": csrf_token("/import-history/"),
            },
        )
        assert r.status_code == 302
        _wait_done(mock_client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["titles"] == ["A", "B"]
        assert captured["from_lang"] == "en"

    def test_post_empty_re_renders_with_flash(self, mock_client, login, csrf_token):
        login("Doc James")
        r = mock_client.post(
            "/import-history/",
            data={"csrf_token": csrf_token("/import-history/")},
        )
        assert r.status_code == 200
        assert b"Provide at least one title" in r.data
