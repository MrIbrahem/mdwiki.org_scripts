"""Per-blueprint route tests with stubbed services.

Each route is exercised end-to-end through ``app.test_client()`` with the
service ``run`` patched to a deterministic stub. We assert:

* GET renders the form (200, contains a CSRF token + key field).
* POST with valid input submits a job and redirects to ``/jobs/<id>``.
* POST with invalid input re-renders the form with a flash (200).
* The kwargs the blueprint passes to the service match the form data.

Service ``run()`` is monkeypatched directly on the module the blueprint
imports it from, so the stubs see exactly the call shape the blueprint
produces.
"""

from __future__ import annotations

import time

import pytest

from main_app.jobs.store import get_store


def _wait_done(client, job_id, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = client.get(f"/jobs/{job_id}.json").get_json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(0.005)
    return data


@pytest.fixture(autouse=True)
def _login_user(login):
    """Default to an allowlisted user; tests that need a different identity
    just call ``login(...)`` themselves."""

    login("Mr. Ibrahem")


# ---------------------------------------------------------------------------
# /dup/
# ---------------------------------------------------------------------------


class TestDup:
    def test_get_renders_form(self, client):
        r = client.get("/dup/")
        assert r.status_code == 200
        assert b'name="start"' in r.data
        assert b"csrf_token" in r.data

    def test_post_starts_job_and_redirects(self, client, csrf_token, monkeypatch):
        from main_app.app_routes.dup import bp_dup  # noqa: F401  ensure import
        from main_app.services import fix_duplicate

        seen: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            seen["called"] = True
            seen["save"] = kw.get("save")
            on_progress(1, 1, "ok")
            return {"fixed": 0}

        monkeypatch.setattr(fix_duplicate, "run", stub)

        r = client.post("/dup/", data={"start": "start", "csrf_token": csrf_token("/dup/")})
        assert r.status_code == 302
        job_id = r.headers["Location"].rsplit("/", 1)[-1]
        data = _wait_done(client, job_id)
        assert data["status"] == "done"
        assert seen == {"called": True, "save": True}

    def test_concurrent_post_returns_existing_job(self, client, csrf_token, monkeypatch):
        from main_app.services import fix_duplicate

        # Slow stub so the first job is still running when the second POST lands.
        def stub(*, on_progress, stop_event, **kw):
            stop_event.wait(timeout=2.0)
            return {}

        monkeypatch.setattr(fix_duplicate, "run", stub)

        r1 = client.post("/dup/", data={"start": "start", "csrf_token": csrf_token("/dup/")})
        r2 = client.post("/dup/", data={"start": "start", "csrf_token": csrf_token("/dup/")})
        assert r1.headers["Location"] == r2.headers["Location"]

        # Cleanup: signal stop so the worker finishes.
        store = get_store()
        for job in store.all():
            job.stop_event.set()


# ---------------------------------------------------------------------------
# /fixred/
# ---------------------------------------------------------------------------


class TestFixred:
    def test_get_renders_form(self, client):
        r = client.get("/fixred/")
        assert r.status_code == 200
        assert b'name="title"' in r.data

    def test_post_with_title_submits_job(self, client, csrf_token, monkeypatch):
        from main_app.services import fixred

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {"scanned": 1}

        monkeypatch.setattr(fixred, "run", stub)

        r = client.post(
            "/fixred/",
            data={"title": "Aspirin", "csrf_token": csrf_token("/fixred/")},
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["title"] == "Aspirin"
        assert captured["save"] is True

    def test_get_with_title_query_also_submits_job(self, client, monkeypatch):
        """Legacy bookmark URLs like /fixred/?title=Foo continue to work."""

        from main_app.services import fixred

        called = []

        def stub(*, on_progress, stop_event, **kw):
            called.append(kw["title"])
            return {}

        monkeypatch.setattr(fixred, "run", stub)

        r = client.get("/fixred/?title=Foo")
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert called == ["Foo"]

    def test_post_without_title_re_renders_form(self, client, csrf_token):
        r = client.post("/fixred/", data={"csrf_token": csrf_token("/fixred/")})
        assert r.status_code == 200
        assert b"Please provide a title" in r.data


# ---------------------------------------------------------------------------
# /redirect/
# ---------------------------------------------------------------------------


class TestRedirect:
    def test_get_renders_form(self, client):
        r = client.get("/redirect/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
        assert b'name="titlelist"' in r.data

    def test_post_single_title_submits_job(self, client, csrf_token, monkeypatch):
        from main_app.services import redirect as redsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(redsvc, "run", stub)
        r = client.post(
            "/redirect/",
            data={"title": "Aspirin", "csrf_token": csrf_token("/redirect/")},
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["titles"] == ["Aspirin"]

    def test_post_titlelist_dedupes_and_strips(self, client, csrf_token, monkeypatch):
        from main_app.services import redirect as redsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(redsvc, "run", stub)
        r = client.post(
            "/redirect/",
            data={
                "titlelist": "A\nB\n\n  A  \nC\n",
                "csrf_token": csrf_token("/redirect/"),
            },
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        # A appears twice in the input; deduped to once. Empties dropped.
        assert captured["titles"] == ["A", "B", "C"]

    def test_post_empty_re_renders_with_flash(self, client, csrf_token):
        r = client.post(
            "/redirect/",
            data={"csrf_token": csrf_token("/redirect/")},
        )
        assert r.status_code == 200
        assert b"Provide at least one title" in r.data


# ---------------------------------------------------------------------------
# /fixref/
# ---------------------------------------------------------------------------


class TestFixref:
    def test_get_renders_form(self, client):
        r = client.get("/fixref/")
        assert r.status_code == 200
        assert b'name="titlelist"' in r.data
        assert b'name="cat"' in r.data
        assert b'name="number"' in r.data

    def test_post_titlelist_submits_job(self, client, csrf_token, monkeypatch):
        from main_app.services import fixref as fsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(fsvc, "run", stub)
        r = client.post(
            "/fixref/",
            data={"titlelist": "A\nB", "csrf_token": csrf_token("/fixref/")},
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["titles"] == ["A", "B"]
        assert captured["category"] is None
        assert captured["number"] is None

    def test_post_category_submits_job(self, client, csrf_token, monkeypatch):
        from main_app.services import fixref as fsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(fsvc, "run", stub)
        r = client.post(
            "/fixref/",
            data={"cat": "Drugs", "csrf_token": csrf_token("/fixref/")},
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["category"] == "Drugs"
        assert captured["titles"] in (None, [])

    def test_post_number_submits_job(self, client, csrf_token, monkeypatch):
        from main_app.services import fixref as fsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(fsvc, "run", stub)
        r = client.post(
            "/fixref/",
            data={"number": "50", "csrf_token": csrf_token("/fixref/")},
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["number"] == 50

    def test_post_all_empty_re_renders_with_flash(self, client, csrf_token):
        r = client.post("/fixref/", data={"csrf_token": csrf_token("/fixref/")})
        assert r.status_code == 200
        assert b"Provide at least one of" in r.data


# ---------------------------------------------------------------------------
# /import-history/  — requires allowlist
# ---------------------------------------------------------------------------


class TestImportHistory:
    def test_unlisted_user_gets_403(self, client, login):
        login("Plain User")
        r = client.get("/import-history/")
        assert r.status_code == 403

    def test_allowlisted_get_renders_form(self, client):
        r = client.get("/import-history/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
        assert b'name="titlelist"' in r.data

    def test_post_submits_job_with_titles_and_from(self, client, csrf_token, monkeypatch):
        from main_app.services import imp

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(imp, "run", stub)
        r = client.post(
            "/import-history/",
            data={
                "titlelist": "A\nB",
                "from": "en",
                "csrf_token": csrf_token("/import-history/"),
            },
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["titles"] == ["A", "B"]
        assert captured["from_lang"] == "en"

    def test_post_empty_re_renders_with_flash(self, client, csrf_token):
        r = client.post(
            "/import-history/",
            data={"csrf_token": csrf_token("/import-history/")},
        )
        assert r.status_code == 200
        assert b"Provide at least one title" in r.data


# ---------------------------------------------------------------------------
# /replace/  — requires allowlist
# ---------------------------------------------------------------------------


class TestReplace:
    def test_unlisted_user_gets_403(self, client, login):
        login("Plain User")
        r = client.get("/replace/")
        assert r.status_code == 403

    def test_allowlisted_get_renders_form(self, client):
        r = client.get("/replace/")
        assert r.status_code == 200
        assert b'name="find"' in r.data
        assert b'name="replace"' in r.data
        assert b'name="listtype"' in r.data

    def test_post_submits_job_with_find_replace_listtype(self, client, csrf_token, monkeypatch):
        from main_app.services import replace as repsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(repsvc, "run", stub)
        r = client.post(
            "/replace/",
            data={
                "find": "foo",
                "replace": "bar",
                "listtype": "newlist",
                "number": "5",
                "csrf_token": csrf_token("/replace/"),
            },
        )
        assert r.status_code == 302
        job_id = r.headers["Location"].rsplit("/", 1)[-1]
        data = _wait_done(client, job_id)
        assert captured["find"] == "foo"
        assert captured["replace"] == "bar"
        assert captured["listtype"] == "newlist"
        assert captured["number"] == 5
        # Job params should NOT contain the literal find/replace strings.
        assert "find" not in data["params"]
        assert data["params"]["find_len"] == 3
        assert data["params"]["replace_len"] == 3

    def test_post_empty_find_re_renders_with_flash(self, client, csrf_token):
        r = client.post(
            "/replace/",
            data={"find": "", "replace": "x", "csrf_token": csrf_token("/replace/")},
        )
        assert r.status_code == 200
        assert b"<code>find</code>" in r.data or b"`find`" in r.data

    def test_replace_log_compat_redirects_to_jobs(self, client):
        r = client.get("/replace/log?id=abc123")
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/jobs/abc123")

    def test_replace_log_without_id_redirects_to_form(self, client):
        r = client.get("/replace/log")
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/replace/")


# ---------------------------------------------------------------------------
# /newupdater/  — synchronous; not a job
# ---------------------------------------------------------------------------


class TestNewupdater:
    def test_get_no_title_renders_form_only(self, client):
        r = client.get("/newupdater/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
        assert b"Save with edit summary" not in r.data

    def test_get_with_title_changes_renders_diff_and_save_button(self, client, monkeypatch):
        from main_app.services.newupdater import UpdaterOutcome
        import main_app.services.newupdater as nu

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title: UpdaterOutcome(kind="changes", old_text="a\n", new_text="b\n"),
        )
        r = client.get("/newupdater/?title=Aspirin")
        assert r.status_code == 200
        assert b"Save with edit summary" in r.data

    def test_get_with_title_no_changes_renders_info(self, client, monkeypatch):
        from main_app.services.newupdater import UpdaterOutcome
        import main_app.services.newupdater as nu

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title: UpdaterOutcome(kind="no_changes", old_text="x", new_text="x"),
        )
        r = client.get("/newupdater/?title=Aspirin")
        assert r.status_code == 200
        assert b"no changes" in r.data

    def test_get_with_title_notext_renders_warning(self, client, monkeypatch):
        from main_app.services.newupdater import UpdaterOutcome
        import main_app.services.newupdater as nu

        monkeypatch.setattr(nu, "work_on_title", lambda title: UpdaterOutcome(kind="notext"))
        r = client.get("/newupdater/?title=Empty")
        assert r.status_code == 200
        assert b"empty" in r.data.lower()

    def test_post_save_calls_save_page_and_redirects(self, client, csrf_token, monkeypatch):
        from main_app.services.newupdater import UpdaterOutcome
        import main_app.services.newupdater as nu

        # Render the diff page so the form has CSRF.
        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title: UpdaterOutcome(kind="changes", old_text="a", new_text="b"),
        )
        save_calls: list[str] = []
        monkeypatch.setattr(
            nu,
            "save_page",
            lambda title, summary="Med updater.": (save_calls.append(title) or (True, "saved")),
        )
        token = csrf_token("/newupdater/?title=Aspirin")
        r = client.post(
            "/newupdater/",
            data={"title": "Aspirin", "csrf_token": token},
        )
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/newupdater/?title=Aspirin")
        assert save_calls == ["Aspirin"]

    def test_post_without_title_redirects_with_flash(self, client, csrf_token, monkeypatch):
        from main_app.services.newupdater import UpdaterOutcome
        import main_app.services.newupdater as nu

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title: UpdaterOutcome(kind="changes", old_text="a", new_text="b"),
        )
        token = csrf_token("/newupdater/?title=Aspirin")
        r = client.post(
            "/newupdater/",
            data={"title": "", "csrf_token": token},
        )
        assert r.status_code == 302
        # follow it, the index should carry the flash
        r2 = client.get(r.headers["Location"])
        assert b"Provide a title" in r2.data
