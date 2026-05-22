# Merge Plan: Legacy PHP + Python tooling → Flask app

> Living document. Source analysis lives in `app_routes_docs/` (one `.md` per
> tool). This plan converts that analysis into a concrete migration roadmap.

---

## 1. Goal & Non-Goals

### 1.1 Goal

Replace the existing PHP entry points (`php/*.php`) and CLI-shaped Python
scripts (`python/*.py`) with **first-class Flask blueprints** under
`flask_app/main_app/app_routes/<tool>/` that:

- accept the same form parameters the PHP files used;
- call backend logic **in-process** (no `shell_exec`, no `toolforge jobs run`,
  no `python3 …` subprocesses);
- run long jobs through a single, uniform background-job mechanism;
- talk to MediaWiki through the existing `flask_app/main_app/newapi`
  package (no parallel `mdapi.py` / `mdwiki_page.py` clients);
- ship reusable templates that extend a shared base layout and use
  Flask-WTF + CSRF for forms.

### 1.2 Non-Goals (this PR / this plan)

- A wholesale rewrite of `python/<script>.py` business logic. The migration
  preserves the existing algorithms; we only extract pure functions and remove
  module-level `sys.argv` / file-IO assumptions.
- Replacing `newapi/`. We **build on top** of it.
- A new auth system. We define an interface (`current_user`, `is_authorized`)
  and back it with a stub now; the real OAuth wiring lands in a follow-up.
- Internationalisation. The PHP UI is English, we keep that.

### 1.3 Success Criteria

- All 7 tools reachable from `/<tool>/` URLs and behave identically to their
  PHP counterparts for happy-path inputs.
- No blueprint shells out to a Python CLI.
- A request can be served without `toolforge jobs run …`, without writing
  `find.txt` / `replace.txt` to disk, and without `importlist.txt`.
- `pytest -q` (added later) passes for at least the two pure-logic adapters
  (`fixred`, `newupdater`).

---

## 2. Tooling Inventory

| URL                | PHP source             | Python source                | Flask blueprint                    | Auth        | Long-running? |
| ------------------ | ---------------------- | ---------------------------- | ---------------------------------- | ----------- | ------------- |
| `/dup/`            | `php/dup.php`          | `python/fix_duplicate.py`    | `app_routes/dup`                   | logged-in   | yes (job)     |
| `/fixred/`         | `php/fixred.php`       | `python/fixred.py`           | `app_routes/fixred`                | logged-in   | yes (per page)|
| `/fixref/`         | `php/fixref.php`       | `python/fixref/start.py`     | `app_routes/fixref`                | logged-in   | yes (job)     |
| `/import-history/` | `php/import-history.php` | `python/imp.py`            | `app_routes/import_history`        | allow-list  | yes (job)     |
| `/newupdater/`     | `php/newupdater.php`   | `python/newupdater.py`       | `app_routes/newupdater`            | logged-in   | sync          |
| `/redirect/`       | `php/redirect.php`     | `python/red.py`              | `app_routes/redirect`              | logged-in   | yes (job)     |
| `/replace/`        | `php/replace/index.php`| `python/find_replace_bot/`   | `app_routes/replace`               | allow-list  | yes (job)     |

“Allow-list” = `["Doc James", "Mr. Ibrahem"]` per the legacy PHP files.

---

## 3. Target Architecture

```
flask_app/
├── app.py                       # WSGI entry (unchanged)
├── main_app/
│   ├── __init__.py              # app factory (extended for new bps & error pages)
│   ├── config.py                # add JOBS_BACKEND, ALLOWLIST_USERS, ENABLE_OAUTH
│   ├── auth/                    # NEW: thin auth surface
│   │   ├── __init__.py
│   │   ├── current_user.py      # current_user(), is_authenticated, is_authorized
│   │   └── decorators.py        # @login_required, @authorized_only
│   ├── jobs/                    # NEW: in-process job runner
│   │   ├── __init__.py
│   │   ├── store.py             # JobStore (in-memory dict + lock; pluggable)
│   │   ├── runner.py            # ThreadPoolExecutor wrapper, status updates
│   │   └── models.py            # Job dataclass: id, tool, status, log, result
│   ├── services/                # NEW: legacy script adapters (pure functions)
│   │   ├── __init__.py
│   │   ├── fix_duplicate.py     # wraps python/fix_duplicate.py logic
│   │   ├── fixred.py            # wraps python/fixred.py logic
│   │   ├── fixref.py            # wraps python/fixref/start.py logic
│   │   ├── imp.py               # wraps python/imp.py logic
│   │   ├── newupdater.py        # wraps python/newupdater.py logic
│   │   ├── redirect.py          # wraps python/red.py logic
│   │   └── replace.py           # wraps python/find_replace_bot logic
│   ├── newapi/                  # existing (untouched)
│   └── app_routes/
│       ├── __init__.py          # register_blueprints (fix duplicate "main" name bug)
│       ├── dup/__init__.py
│       ├── fixred/__init__.py
│       ├── fixref/__init__.py
│       ├── import_history/__init__.py
│       ├── main/__init__.py
│       ├── newupdater/__init__.py
│       ├── redirect/__init__.py
│       └── replace/__init__.py
└── templates/
    ├── _base.html              # NEW: shared layout that includes header+footer
    ├── _macros.html            # NEW: form helpers (input, textarea, csrf, flash)
    ├── header.html             # existing (light edits to use url_for)
    ├── footer.html             # existing
    ├── jobs/status.html        # NEW: generic job status page
    ├── dup.html                # rewritten to extend _base.html
    ├── fixred.html             # rewritten to extend _base.html
    ├── fixref.html             # rewritten to extend _base.html
    ├── import-history.html     # rewritten to extend _base.html
    ├── newupdater.html         # rewritten to extend _base.html
    ├── redirect.html           # rewritten to extend _base.html
    └── replace.html            # rewritten to extend _base.html
```

### 3.1 Layering rules

```
blueprint  ─►  service  ─►  newapi  ─►  MediaWiki
            \                        ▲
             └► jobs.runner ─────────┘   (for async tools)
auth ──┐
       └► used as decorator on blueprint endpoints
```

- A blueprint **never** imports `python/*` directly. Always via
  `main_app/services/<tool>.py`.
- A service module exposes pure functions taking primitives (`title: str`,
  `titles: list[str]`, `from_lang: str | None`, `save: bool`). It returns a
  domain `Result` dataclass, never `sys.exit`s, never writes files for IPC.
- A service module is allowed to import from `python/*` *only* through a
  thin compatibility wrapper that does the legacy-script-side adaptation. This
  keeps the diff small while we delete the CLI entry points.
- The job runner is the **only** place that knows about threads / queues. The
  service stays synchronous and reentrant.

### 3.2 Jobs subsystem

`Job` dataclass: `id`, `tool`, `params`, `status` (`pending|running|done|error`),
`progress` (`{done:int, total:int}`), `log` (last N lines), `result`,
`created_at`, `updated_at`, `submitted_by`.

`JobStore` interface (`get`, `put`, `update`, `list_for_user`) backed by an
in-memory dict guarded by a lock. The interface is the seam where we later
swap in SQLite/Redis without touching blueprints.

`JobRunner.submit(tool: str, fn: Callable, **params) -> job_id` runs `fn` in a
`ThreadPoolExecutor` and pipes log lines into `Job.log` via a per-job
`logging.Handler`. Caps: `max_workers=int(JOBS_MAX_WORKERS or 2)`,
`log_max_lines=200`.

A generic endpoint `/jobs/<id>` renders `jobs/status.html`. A JSON variant
`/jobs/<id>.json` powers polling. This replaces the legacy
`replace-log.php?id={nn}` page and the “queued” strings the current stubs
return.

### 3.3 Authentication / authorization

We do **not** implement full OAuth in this PR. We add:

- `auth.current_user() -> User | None` reading `session["username"]`.
- `auth.is_authenticated()` and `auth.is_authorized(user)`.
- `@login_required` (302 to a login placeholder if missing).
- `@authorized_only(allowlist=settings.allowlist_users)` returning **403 with
  a friendly “Access denied” template** for `import-history` and `replace`.

For local testing, a hidden `?dev_user=Mr. Ibrahem` query writes the username
into `session` only when `settings.is_localhost(request.host)` is `True`.

When the OAuth integration lands later, only `auth/current_user.py` changes.

---

## 4. Per-Route Migration Plan

Each section follows the same shape: **inputs → contract → service signature →
flow → edge cases → tests**.

### 4.1 `/dup/` — fix duplicate redirects

- **Inputs:** `start` (POST submit). No other fields.
- **Auth:** `@login_required`.
- **Service:** `services.fix_duplicate.run(*, save: bool, offset: int = 0,
  on_progress=None) -> JobResult`. Iterates `DoubleRedirects`, for each pair
  runs `fix_dup(from_title, to_title)` lifted out of
  `python/fix_duplicate.py`. Returns counts of (`scanned`, `fixed`,
  `unchanged`, `errors`).
- **Flow:**
  1. GET `/dup/` → render form (with auth-aware “please log in” banner if
     anonymous).
  2. POST `/dup/` with `start=start` → `JobRunner.submit("dup",
     services.fix_duplicate.run, save=True)` → 302 to `/jobs/<id>`.
- **Refactor needed in legacy script:** strip the module-level
  `sys.argv` parsing for `-offset:N`; promote `offset` to a parameter on
  `run(...)`. The `load_main_api()` `lru_cache` stays.
- **Edge cases:** double-submit guard via `JobRunner.find_active("dup")`; if
  one is already running, render the existing job page instead of creating a
  second.

### 4.2 `/fixred/` — fix redirects in page text

- **Inputs:** `title` (GET). May be `"all"`.
- **Auth:** `@login_required`.
- **Service:** `services.fixred.run(*, title: str, save: bool = True,
  on_progress=None) -> JobResult`. Calls a refactored `treat_page(title)` (we
  add it to `services.fixred`, copying the body from `python/fixred.py` and
  removing `sys.argv` reads). When `title == "all"` it pulls
  `NewApi.Get_All_pages(apfilterredir="nonredirects")`.
- **Flow:** GET with no query → form; GET with `title=…` → submit job, 302
  to `/jobs/<id>`. We keep GET for back-compat (legacy bookmarks like
  `/fixred/?title=Aspirin`).
- **Refactor:** `replace_links2`, `Get_page_links`, `find_redirects` move to
  `services/fixred.py`. They take wiki client objects, not globals.
- **Edge cases:** sanitise `title` (`+` → space → trim); refuse empty titles
  with `flash(...)`.

### 4.3 `/fixref/` — normalise references

- **Inputs:** `titlelist` (textarea), `number` (int) — POST. Optionally `cat`
  (new field).
- **Auth:** `@login_required`.
- **Service:** `services.fixref.run(*, titles: list[str] | None = None,
  number: int | None = None, category: str | None = None, save: bool = True,
  on_progress=None) -> JobResult`. Internally:
  - If `titles` non-empty → iterate them.
  - Else if `category` → iterate category members via
    `AllAPIS.CatDepth(category)`.
  - Else if `number` → iterate `Get_All_pages(limit_all=number)`.
  - For each page call `fix_ref_template(text)` from
    `python/fixref/` (lifted into the service).
- **Flow:** GET → form; POST → service → 302 `/jobs/<id>`.
- **Refactor:** drop the `-file:` temp-file mechanism entirely. The blueprint
  splits the textarea on newlines and passes the list directly.
- **Cap:** `MAX_PAGES_FIXREF = 20000` constant kept (was `thenumbers[1]`).
- **Validation:** at least one of (`titlelist`, `number`, `cat`) must be set.

### 4.4 `/import-history/` — import enwiki history

- **Inputs:** `title` (single) **or** `titlelist` (textarea); optional `from`
  (source language). POST.
- **Auth:** `@authorized_only(allowlist)`.
- **Service:** `services.imp.run(*, titles: list[str], from_lang: str = "en",
  save: bool = True, on_progress=None) -> JobResult`. Per title:
  `MainPage(title, from_lang, family="wikipedia").import_page(family="mdwiki")`
  then re-save body to restore text. Fallback target on failure:
  `User:Mr._Ibrahem/<title>`.
- **Flow:** GET → form (or 403 page); POST → service → 302 `/jobs/<id>`.
- **Refactor:** drop `importlist.txt` write; pass the list in memory.
- **Validation:** if `titlelist` given, split on newlines, deduplicate, strip
  empties; cap to `MAX_IMPORT_TITLES = 500`.

### 4.5 `/newupdater/` — medical content updater

- **Inputs:** `title` (GET, required), `save` (GET checkbox).
- **Auth:** `@login_required`.
- **Behaviour:** **synchronous** (legacy is fast; no toolforge job).
- **Service:** `services.newupdater.work_on_title(title) ->
  UpdaterOutcome(kind, old_text, new_text)` where `kind ∈ {notext, no_changes,
  changes}`. Plus `services.newupdater.save_page(title, new_text) -> bool`.
- **Flow:**
  1. GET with no `title` → render form.
  2. GET with `title` and **no** `save` → call `work_on_title`; render diff
     view + a CSRF-protected POST form pointing back to `/newupdater/?title=…`
     with `save=1`.
  3. POST/GET with `save=1` → call `save_page`; render a success / error
     panel.
- **Refactor:** drop `save_cash` / `updatercash/`; the new text is held in the
  rendered page (and round-trips via the form), or stored in a per-session
  cache keyed by `title`. We **do not** POST to `mdwiki.org/w/index.php`
  anymore — saving is in-process.

### 4.6 `/redirect/` — copy redirects from enwiki

- **Inputs:** `title` (single) **or** `titlelist` (textarea). POST.
- **Auth:** `@login_required`.
- **Service:** `services.redirect.run(*, titles: list[str], save: bool = True,
  on_progress=None) -> JobResult`. Per title:
  `get_red(title)` (lifted from `python/red.py`), filter via `valid_title`,
  for each redirect not yet on mdwiki, create
  `#redirect [[<target>]]`.
- **Flow:** GET → form; POST → service → 302 `/jobs/<id>`.
- **Refactor:** drop `redirectlist.txt`.

### 4.7 `/replace/` — find & replace

This is the biggest refactor.

- **Inputs:** `find` (textarea, required), `replace` (textarea, required, may
  be empty), `number` (int), `listtype` (`newlist|oldlist`). POST.
- **Auth:** `@authorized_only(allowlist)`.
- **Service:** `services.replace.run(*, find: str, replace: str, number: int |
  None, listtype: Literal["newlist","oldlist"], on_progress=None,
  stop_event=None) -> JobResult`. Logic from `find_replace_bot/one_job.py`
  lifted in: titles via `Search(find)` for `newlist`, `Get_All_pages()` for
  `oldlist`. For each page: load text → `text.replace(find, replace, count)` →
  if changed, save. `on_progress` reports `{done, total, last_title}`;
  `stop_event` is a `threading.Event` to make `/jobs/<id>/stop` work.
- **Flow:** GET → form; POST → submit job → 302 `/jobs/<id>`.
- **Refactor:** delete the file-based job dispatch entirely. No
  `replace/find/{nn}/find.txt`, no `done.txt`, no `log.txt`, no `stop.txt`.
  These are replaced by `Job.log`, `Job.status`, and `Job.stop_event`.
- **Compat shim (optional):** keep a redirect from
  `/replace-log.php?id=<nn>` → `/jobs/<nn>` so old links still work.

---

## 5. Templates

### 5.1 New `_base.html`

Wraps the existing `header.html` and `footer.html` and exposes Jinja blocks:

```jinja
{% block title %}{% endblock %}
{% block content %}{% endblock %}
{% block scripts %}{% endblock %}
```

### 5.2 Macros (`_macros.html`)

- `csrf()` → `<input type="hidden" name="csrf_token" value="…">`
- `flash_messages()` → renders `get_flashed_messages(with_categories=True)`
  using bootstrap alert classes already loaded in `header.html`.
- `auth_gate(user)` → renders the “please log in” / “access denied”
  panels.

### 5.3 Per-tool template changes (common)

For every existing template:

1. Replace `<form action='X.php'>` with `<form method=POST
   action="{{ url_for('<bp>.<endpoint>') }}">`.
2. Inject `{{ csrf() }}` inside every form.
3. Add `{{ flash_messages() }}` at the top of `{% block content %}`.
4. When `result` is a `Job`, link to `{{ url_for('jobs.status',
   job_id=result.id) }}`.

### 5.4 New `jobs/status.html`

Displays job metadata + last-N log lines with a meta refresh fallback and a
small JS poller hitting `/jobs/<id>.json`.

---

## 6. Backend (legacy script) refactor strategy

The fastest, safest path is a **lift-and-shim** rather than a clean rewrite:

1. Create `flask_app/main_app/services/<tool>.py`.
2. Copy the relevant functions from `python/<tool>.py` into the service. Drop
   any module-level `sys.argv` reads; promote those values to parameters of a
   new `run(...)` entry point.
3. Replace `from mdapi import …` and `from mdwiki_page import …` with the
   `newapi` equivalents (`AllAPIS`, `MainPage`, `NewApi`). The mapping is:
   - `mdapi.GetPageText(t)` → `MainPage(t, "www", family="mdwiki").get_text()`
   - `mdapi.page_put(text, summary, t)` → `MainPage(t, ...).save(newtext=text,
     summary=summary)`
   - `mdwiki_page.NewApi(...)` → `AllAPIS(...).NewApi()`
4. Add a `_load_api()` helper using `functools.lru_cache(maxsize=1)` reading
   credentials from env (already used by `python/fix_duplicate.py`).
5. Leave `python/*` files in place during the migration. Once all blueprints
   are wired and tests pass, delete them in a follow-up PR.

---

## 7. Configuration

Additions to `main_app/config.py` (`Settings` dataclass):

| Field             | Env var                  | Default | Notes                                       |
| ----------------- | ------------------------ | ------- | ------------------------------------------- |
| `allowlist_users` | `ALLOWLIST_USERS`        | `"Doc James,Mr. Ibrahem"` | comma-sep, used by `import-history` & `replace` |
| `enable_oauth`    | `ENABLE_OAUTH`           | `false` | when `false`, `/auth` falls back to dev-mode |
| `jobs_max_workers`| `JOBS_MAX_WORKERS`       | `2`     | thread pool size                            |
| `jobs_log_lines`  | `JOBS_LOG_LINES`         | `200`   | rolling per-job log buffer size             |
| `wiki_username`   | `WIKIPEDIA_HIMO_USERNAME`| –       | already used by `fix_duplicate.py`          |
| `wiki_password`   | `MDWIKI_HIMO_PASSWORD`   | –       | already used by `fix_duplicate.py`          |

The OAuth env-var hard-fail in `_load_oauth_config()` is **softened** behind
`ENABLE_OAUTH`. When it is `false` (default for local), missing OAuth vars
log a warning instead of raising. This unblocks `flask run` without prod
secrets and is gated to non-prod hosts via `is_localhost`.

---

## 8. Testing strategy

- **Unit tests** (`pytest`):
  - `tests/services/test_fixred.py` — feed it a stubbed wiki client, assert
    `treat_page("Aspirin")` produces the expected save.
  - `tests/services/test_newupdater.py` — assert `work_on_title` returns the
    three documented outcomes.
  - `tests/jobs/test_runner.py` — submit a no-op fn, assert status
    transitions.
- **Route tests** with `app.test_client()`:
  - GET `/dup/` returns 200 and renders the form.
  - POST `/replace/` without auth returns 403 and the access-denied template.
  - GET `/jobs/<id>.json` for an unknown id returns 404.
- **Dependencies stubbed:** the wiki client is replaced by a fake that
  records calls; nothing reaches the network from CI.

A minimal `conftest.py` builds the app via `create_app()` with
`ENABLE_OAUTH=false`, `FLASK_SECRET_KEY=test`,
`OAUTH_ENCRYPTION_KEY=test`.

---

## 9. Phased delivery

**Phase 1 — this PR (scaffolding + plan)**
- Land this `docs/merge-plan.md`.
- Add `auth/`, `jobs/` (in-memory), `services/` skeletons.
- Fix the duplicate `Blueprint("main", ...)` name collision (each blueprint
  must use a unique name like `bp_dup = Blueprint("dup", …)`).
- Add `_base.html`, `_macros.html`, `jobs/status.html`.
- End-to-end migrate **one** route — `/dup/` — as the reference
  implementation (it is the simplest: one button, one job).
- Soften OAuth requirement behind `ENABLE_OAUTH`.

**Phase 2** — migrate `/fixred/` and `/newupdater/` (no jobs / sync, easy
wins after the auth + service pattern is set).

**Phase 3** — migrate `/redirect/` and `/fixref/` (jobs with list inputs).

**Phase 4** — migrate `/import-history/` (auth allow-list path) and
`/replace/` (largest refactor + stop signal).

**Phase 5** — delete `php/`, delete `python/<tool>.py`, delete the file-based
`replace/find/<nn>/` pipeline, add the `/replace-log.php` compat redirect.

**Phase 6** — wire real OAuth for `current_user`. Replace the in-memory
`JobStore` with SQLite if persistence is needed across restarts.

---

## 10. Risk register & mitigations

| Risk                                                                  | Mitigation                                                                                  |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Long-running jobs block the WSGI worker                              | All non-trivial work goes through `JobRunner` (ThreadPoolExecutor); blueprints return 302. |
| Threaded jobs share global state in `python/*` modules               | Lift to `services/`; remove module-level mutable globals; document concurrency assumptions.|
| Lost progress when the worker restarts                               | In-memory store is documented as ephemeral; SQLite swap-in is a 1-file change.             |
| Wiki rate limits while a job runs                                    | Reuse `NewApi` chunking + `tqdm` patterns already in `bot_api.py`.                         |
| Authorization bypass for `replace` / `import-history`                | `@authorized_only` decorator + 403 template + tests asserting unauthenticated GET = 403.   |
| CSRF rejection of legacy bookmark URLs (`/fixred/?title=…`)          | `/fixred/` keeps GET; `csrf_exempt` not needed because GET has no side-effect (job submit ↔ POST). |
| Existing `Blueprint("main", …)` collision when registering all blueprints | Phase-1 task: rename each to its unique name. Will surface as `AssertionError: A name collision …`. |

---

## 11. File-by-file change list (Phase 1)

**Add**
- `docs/merge-plan.md` (this file)
- `flask_app/main_app/auth/__init__.py`
- `flask_app/main_app/auth/current_user.py`
- `flask_app/main_app/auth/decorators.py`
- `flask_app/main_app/jobs/__init__.py`
- `flask_app/main_app/jobs/models.py`
- `flask_app/main_app/jobs/store.py`
- `flask_app/main_app/jobs/runner.py`
- `flask_app/main_app/services/__init__.py`
- `flask_app/main_app/services/fix_duplicate.py`
- `flask_app/main_app/app_routes/jobs/__init__.py`  (status + json endpoints)
- `flask_app/templates/_base.html`
- `flask_app/templates/_macros.html`
- `flask_app/templates/jobs/status.html`

**Edit**
- `flask_app/main_app/__init__.py` — register `bp_jobs`, expose
  `current_user` to templates via context processor.
- `flask_app/main_app/config.py` — add new settings, soften OAuth check.
- `flask_app/main_app/app_routes/__init__.py` — register `bp_jobs`; verify
  unique blueprint names.
- `flask_app/main_app/app_routes/dup/__init__.py` — wire to service + jobs.
- `flask_app/main_app/app_routes/<other>/__init__.py` — rename Blueprint
  name from `"main"` to something unique (no behaviour change yet).
- `flask_app/templates/dup.html` — extend `_base.html`, use `url_for`, csrf,
  flash.

**Untouched (Phase 1)**
- `python/*` (will be progressively shrunk in later phases).
- `php/*` (will be removed in Phase 5).
- `flask_app/main_app/newapi/*`.

---

## 12. Open questions

1. **Single-instance vs. multi-instance deploy.** The in-memory `JobStore`
   only works on a single worker. If we deploy with multiple uwsgi/gunicorn
   workers, jobs become invisible across workers. Decision: document
   single-worker for now; SQLite swap is the upgrade path.
2. **Real auth source.** Toolforge OAuth vs. MediaWiki OAuth vs. cookie pass-
   through? Out of scope here; the `auth/` interface insulates us.
3. **Throttling.** Should `JobRunner` reject duplicate concurrent jobs per
   tool, or queue them? Phase-1 default: reject (return the existing
   `/jobs/<id>` instead).
