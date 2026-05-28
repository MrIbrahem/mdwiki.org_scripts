# MDWiki Tools — Flask Application

## Project Overview

A Flask web application deployed on **Wikimedia Toolforge** that provides administrative and content-management tools for [mdwiki.org](https://mdwiki.org), a medical wiki. The app enables authenticated MediaWiki users to run batch operations on wiki pages — fixing redirects, normalizing references, importing revision history, performing find-and-replace, and updating medical content templates.

### Main Modules

| Module                   | Purpose                                                    |
| ------------------------ | ---------------------------------------------------------- |
| `main_app/config/`       | Environment-based configuration (frozen dataclasses)       |
| `main_app/core/`         | Fernet encryption, cookie signing                          |
| `main_app/db/`           | SQLAlchemy models + CRUD services (users, tokens, jobs)    |
| `main_app/api_services/` | MediaWiki API wrappers (`mwclient`)                        |
| `main_app/app_routes/`   | Flask Blueprints (auth, jobs, updater, fixred)             |
| `main_app/new_jobs/`     | Thread-based background job runner + 8 workers             |
| `main_app/shared/`       | Domain logic (wikitext processing, template normalization) |
| `main_app/su_services/`  | User auth helpers + job file I/O                           |
| `main_app/utils/`        | Validation helpers                                         |

### Technologies & Dependencies

-   **Python 3.13+**, **Flask 3.x**, **Flask-SQLAlchemy**, **Flask-Migrate**, **Flask-WTF**
-   **SQLAlchemy** ORM with **PyMySQL** (MySQL) / SQLite (tests)
-   **mwclient** — MediaWiki API client
-   **wikitextparser** — Wikitext parsing and manipulation
-   **cryptography** (Fernet) — OAuth token encryption
-   **mwoauth** — MediaWiki OAuth 1.0a
-   **itsdangerous** — Signed cookies and state tokens
-   **uWSGI** — Production deployment

## Architecture & Code Quality Review

### Code Organization

The project follows the **application factory pattern** with a clean layered architecture:

```
flask_app/
├── app.py                 # Development entry point (dotenv, colorlog)
├── app1.py                # Production entry point (no dotenv)
├── logger_config.py       # Logging setup (console + file handlers)
├── uwsgi.ini              # uWSGI production config
├── static/                # CSS/JS assets
├── templates/             # Jinja2 templates
│   ├── base.html, index.html, _navbar.html
│   ├── jobs_templates/    # Legacy job templates
│   └── new_jobs_templates/# Per-worker-type templates
└── main_app/              # Core application package
    ├── __init__.py         # create_app() factory
    ├── extensions.py       # SQLAlchemy + Migrate instances
    ├── config/             # Frozen dataclass settings
    ├── core/               # Security (encryption, cookies)
    ├── db/                 # Models + services
    ├── api_services/       # MediaWiki API layer
    ├── app_routes/         # Flask Blueprints
    ├── new_jobs/           # Background workers
    ├── shared/             # Business logic
    ├── su_services/        # Auth + file services
    └── utils/              # Validation
```

### Design Patterns

-   **Application Factory** — `create_app(config_class)` in `main_app/__init__.py`
-   **Blueprint Pattern** — 5 blueprints: `bp_auth`, `bp_main`, `bp_public_jobs`, `bp_newupdater`, `bp_fixred`
-   **Repository Pattern** — Service modules in `db/services/` abstract database operations
-   **Template Method** — `BaseObjectsJobWorker` defines `before_run() → process() → after_run()` lifecycle
-   **Strategy Pattern** — Worker registry maps job types to entry functions
-   **Singleton** — `settings` via `@lru_cache(maxsize=1)`

### Maintainability

Good structural separation, but the `shared/` package contains deeply nested wikitext processing logic with minimal documentation. Configuration is well-organized with frozen dataclasses.

### Readability

Generally good use of type hints and docstrings. Some files in `shared/new_updater/` mix Arabic and English comments. Naming conventions are mostly consistent (snake_case).

### Scalability

The thread-based job runner is simple but limited — no job queue, no persistence across restarts, no horizontal scaling. Suitable for the current Toolforge single-instance deployment.

## Strengths

-   **Clean application factory** with proper Flask conventions
-   **Immutable configuration** via frozen dataclasses prevents accidental mutation
-   **CSRF protection** enabled by default with Flask-WTF
-   **Fernet encryption** for stored OAuth credentials — strong symmetric encryption
-   **Rate limiting** on auth endpoints (thread-safe, in-memory)
-   **Background job system** with cancellation support (local `Event` + DB status)
-   **Comprehensive error handling** in `MwClientPage` with specific MediaWiki exception types
-   **Proper type hints** throughout most of the codebase
-   **Separate dev/prod entry points** with appropriate logging levels
-   **`WatchedFileHandler`** for log rotation compatibility

## Weaknesses

-   **No `requirements.txt` or `pyproject.toml`** — dependencies are undocumented
-   **Zero test coverage** — no test files exist
-   **`__pycache__` directories** present in the repository
-   **Code duplication** — `UpdaterOutcome` dataclass defined in both `fixred_one.py` and `newupdater/worker.py`
-   **Complex business logic** in `shared/new_updater/` with poor documentation
-   **Mixed comments** — Arabic comments without English translations in some files
-   **Empty packages** — `api_services/utils/` is effectively dead code
-   **No CI/CD** configuration
-   **No linting or type-checking** configuration

## Critical Issues

> **Warning**: These issues can cause runtime failures or security concerns.

### 1. Broken Function — `query_api.py:get_template_pages_newapi()`

```python
# Line 28-29 in api_services/query_api.py
api = None  # get_api()
results = api.NewApi().post_continue(params, "query", _p_="pages", p_empty=[])
```

This will crash with `AttributeError: 'NoneType' object has no attribute 'NewApi'`.

### 2. Thread-Safety Issue in `crypto.py`

```python
# Line 26-27 in core/crypto.py
# with _fernet_lock:   # <-- LOCK IS COMMENTED OUT
_fernet = Fernet(key_bytes)
```

The global `_fernet` singleton is initialized lazily without thread-safe locking. Under concurrent requests, this could lead to race conditions.

### 3. Memory Leak in Rate Limiter

```python
# app_routes/auth/rate_limit.py
self._hits: Dict[str, Deque[datetime]] = {}
```

The `_hits` dict grows unboundedly — stale keys are never evicted. Over time, this will consume increasing memory.

### 4. Potential Path Traversal in Job Results

```python
# app_routes/new_jobs.py line 265
@bp_public_jobs.get("/read-job-result-file/<path:result_file>")
def read_job_result_file(result_file: str):
    result_data = load_job_result(result_file)
```

The `result_file` parameter is passed directly to file loading without sanitization.

### 5. Missing Authorization on Delete

```python
# app_routes/new_jobs.py line 259
# @admin_required   # <-- COMMENTED OUT
@bp_public_jobs.post("/<string:job_type>/<int:job_id>/delete")
def delete_job(job_type: str, job_id: int):
```

### 6. No Database Session Rollback

Service functions call `db.session.commit()` without try/except rollback blocks. Failed commits leave the session in an inconsistent state.

## Areas That Need Attention

-   [ ] Add `requirements.txt` with pinned dependencies
-   [ ] Add `.gitignore` for `__pycache__`, `*.pyc`, `.env`
-   [ ] Add pytest test suite (at minimum for config, crypto, and auth flows)
-   [ ] Fix the broken `get_template_pages_newapi()` function
-   [ ] Uncomment the thread-safety lock in `crypto.py`
-   [ ] Add path sanitization for job result file serving
-   [ ] Restore `@admin_required` on the delete job endpoint
-   [ ] Add proper error pages (not just `index.html` for all errors)
-   [ ] Add health check endpoint for monitoring
-   [ ] Document the environment variables (`.env.example`)

## Improvement Plan

### Quick Wins (1-2 days)

1. Add `requirements.txt` with all dependencies pinned
2. Add `.gitignore` for Python artifacts
3. Fix the broken `get_template_pages_newapi()` — either implement or remove
4. Uncomment the thread-safety lock in `crypto.py`
5. Add `@admin_required` back to the delete job route
6. Add path validation in `load_job_result()`

### Medium-Term (1-2 weeks)

1. Add pytest test suite with SQLite in-memory database
2. Consolidate duplicate `UpdaterOutcome` dataclasses into a shared module
3. Add proper DB session rollback handling in all service functions
4. Add ruff for linting and mypy for type checking
5. Add an `.env.example` documenting all required/optional variables
6. Implement proper error pages for 400/403/404/500

### Long-Term (1-2 months)

1. Migrate from daemon threads to **Celery** or **asyncio** for job processing
2. Add **Redis** for rate limiting and session caching
3. Add **OpenTelemetry** for observability
4. Refactor `shared/new_updater/` — break down complex functions, add documentation
5. Add CI/CD pipeline (GitHub Actions)
6. Containerize with Docker for consistent deployments

## Comprehensive Review

| Metric                   | Score    | Notes                                                   |
| ------------------------ | -------- | ------------------------------------------------------- |
| **Overall Rating**       | **6/10** | Functional but needs hardening                          |
| **Production Readiness** | Moderate | Running on Toolforge, but lacks tests and monitoring    |
| **Technical Debt**       | Moderate | Legacy scripts being refactored into Flask              |
| **Risk Assessment**      | Medium   | Auth/encryption solid; lack of tests creates risk       |
| **Maintainability**      | 5/10     | Good structure, but complex undocumented business logic |
| **Test Coverage**        | 0/10     | No tests exist                                          |
| **Documentation**        | 4/10     | Some docstrings, no external docs                       |
| **Security**             | 7/10     | CSRF, encryption, rate limiting present; some gaps      |
