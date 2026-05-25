""" """

from __future__ import annotations

# ---------------------------------------------------------------------------
# /newupdater/  — synchronous; not a job
# ---------------------------------------------------------------------------


class TestNewupdater:
    def test_get_no_title_renders_form_only(self, client, login):
        login("Doc James")
        r = client.get("/newupdater/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
        assert b"Save with edit summary" not in r.data

    def test_get_with_title_changes_renders_diff(self, client, login, monkeypatch):
        import flask_app.main_app.public_jobs_workers.newupdater as nu
        from flask_app.main_app.public_jobs_workers.newupdater import UpdaterOutcome

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title, save=0, summary="Med updater.": UpdaterOutcome(
                kind="changes", old_text="a\n", new_text="b\n"
            ),
        )
        login("Doc James")
        r = client.get("/newupdater/?title=Aspirin")
        assert r.status_code == 200
        assert b"Proposed changes" in r.data

    def test_get_with_title_no_changes_renders_info(self, client, login, monkeypatch):
        import flask_app.main_app.public_jobs_workers.newupdater as nu
        from flask_app.main_app.public_jobs_workers.newupdater import UpdaterOutcome

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title, save=0, summary="Med updater.": UpdaterOutcome(kind="no_changes", old_text="x", new_text="x"),
        )
        login("Doc James")
        r = client.get("/newupdater/?title=Aspirin")
        assert r.status_code == 200
        assert b"no changes" in r.data

    def test_get_with_title_notext_renders_warning(self, client, login, monkeypatch):
        import flask_app.main_app.public_jobs_workers.newupdater as nu
        from flask_app.main_app.public_jobs_workers.newupdater import UpdaterOutcome

        monkeypatch.setattr(
            nu, "work_on_title", lambda title, save=0, summary="Med updater.": UpdaterOutcome(kind="notext")
        )
        login("Doc James")
        r = client.get("/newupdater/?title=Empty")
        assert r.status_code == 200
        assert b"empty" in r.data.lower()

    def test_get_with_save_calls_work_on_title_with_save(self, client, login, monkeypatch):
        import flask_app.main_app.public_jobs_workers.newupdater as nu
        from flask_app.main_app.public_jobs_workers.newupdater import UpdaterOutcome

        calls: list[dict] = []

        def spy(title, save=0, summary="Med updater."):
            calls.append({"title": title, "save": save})
            return UpdaterOutcome(kind="no_changes", old_text="x", new_text="x")

        monkeypatch.setattr(nu, "work_on_title", spy)
        login("Doc James")
        r = client.get("/newupdater/?title=Aspirin&save=1")
        assert r.status_code == 200
        assert len(calls) == 1
        assert calls[0]["title"] == "Aspirin"
        assert calls[0]["save"] == 1

    def test_get_without_title_shows_empty_form(self, client, login, monkeypatch):
        import flask_app.main_app.public_jobs_workers.newupdater as nu
        from flask_app.main_app.public_jobs_workers.newupdater import UpdaterOutcome

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title, save=0, summary="Med updater.": UpdaterOutcome(kind="changes", old_text="a", new_text="b"),
        )
        login("Doc James")
        r = client.get("/newupdater/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
