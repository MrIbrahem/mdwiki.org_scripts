# main_app — Core Application Package

## Project Overview

`main_app` is the core Python package implementing the Flask application factory and all business logic for the MDWiki tools platform. It follows the application factory pattern and is organized into clean subpackages with well-defined responsibilities.

### Main Modules

| Subpackage      | Purpose                                                       |
| --------------- | ------------------------------------------------------------- |
| `config/`       | Frozen dataclass settings loaded from environment variables   |
| `core/`         | Fernet encryption for OAuth tokens, cookie signing            |
| `db/`           | SQLAlchemy models (UserToken, AdminUser, Job) + CRUD services |
| `api_services/` | MediaWiki API wrappers (mwclient-based)                       |
| `app_routes/`   | Flask Blueprints (auth, main, jobs, newupdater, fixred)       |
| `new_jobs/`     | Thread-based background job runner + 8 worker implementations |
| `shared/`       | Domain logic — wikitext processing, template normalization    |
| `su_services/`  | User authentication helpers + job result file I/O             |
| `utils/`        | Input validation helpers                                      |

### Technologies

-   **Flask 3.x** with application factory pattern
-   **Flask-SQLAlchemy** + **Flask-Migrate** for database ORM
-   **Flask-WTF** for CSRF protection
-   **mwclient** for MediaWiki API interaction
-   **wikitextparser** for wikitext manipulation
-   **cryptography.Fernet** for symmetric encryption
-   **mwoauth** for MediaWiki OAuth 1.0a

## Architecture & Code Quality Review

### Application Factory (`__init__.py`)

```python
def create_app(config_class: Type) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class())
    csrf = CSRFProtect(app)
    _db.init_app(app)
    migrate.init_app(app, _db)
    init_db(app, _db)
    register_blueprints(app)
    return app
```

Key design decisions:

-   Config class is injected (not auto-detected) — explicit and testable
-   CSRF protection enabled globally via Flask-WTF
-   Database tables auto-created on startup (`init_db`)
-   Context processor injects `current_user` into all templates
-   Custom error handlers for 400, 403, 404, 405, 500, CSRF errors

### Extension Instantiation (`extensions.py`)

```python
db = SQLAlchemy(model_class=BaseModel, session_options={"expire_on_commit": False})
migrate = Migrate()
```

-   `BaseModel.to_dict()` provides generic serialization for all models
-   `expire_on_commit=False` keeps objects accessible after commit without re-querying
-   Extensions are instantiated here (not in `__init__.py`) to prevent circular imports

### Blueprint Registration

5 blueprints registered in `app_routes/__init__.py`:

| Blueprint        | URL Prefix    | Purpose                     |
| ---------------- | ------------- | --------------------------- |
| `bp_auth`        | `/`           | OAuth login/logout/callback |
| `bp_main`        | `/`           | Index page, favicon         |
| `bp_public_jobs` | `/new_jobs`   | Job management dashboard    |
| `bp_newupdater`  | `/newupdater` | Medical content updater     |
| `bp_fixred`      | `/fixred`     | Single-page redirect fixer  |

## Testing

```bash
pytest tests/ --cov=flask_app/main_app
```

## Strengths

-   **Clean separation of concerns** across subpackages
-   **Immutable configuration** via frozen dataclasses
-   **Proper CSRF protection** via Flask-WTF
-   **Custom `BaseModel.to_dict()`** for consistent serialization
-   **Context processor** injects user info into all templates automatically
-   **`WatchedFileHandler`** for log rotation compatibility
-   **Application factory** accepts config class — easy to test with `TestingConfig`
-   **`expire_on_commit=False`** matches existing session behavior

## Weaknesses

-   **No dependency injection** — tight coupling to `settings` singleton
-   **`shared/` package** contains complex wikitext processing with poor documentation
-   **Worker objects partially consolidated** — `SharedworkerObject` in `new_jobs/shared_objects.py` replaces per-worker dataclasses for 4 workers; 3 workers retain local objects
-   **No middleware** for request logging, timing, or metrics
-   **`load_auth_payload`** passes encrypted bytes without explicit decryption context
-   **All error handlers** render `index.html` — no dedicated error pages
-   **No health check** endpoint

## Critical Issues

> **Warning**: Thread-safety and performance concerns.

### 1. Fernet Singleton Race Condition

`core/crypto.py` initializes the global `_fernet` lazily without thread-safe locking (lock is commented out).

### 2. `is_job_cancelled()` Performance

`db/services/jobs_service.py` calls `db.session.refresh(record)` on every cancellation check — this hits the database in tight loops within workers.

### 3. Error Pages

All error handlers render `index.html` with a flash message — users get no useful error information.

## Areas That Need Attention

-   [ ] Add health check endpoint (`/healthz`)
-   [ ] Create dedicated error templates
-   [ ] Add request logging middleware
-   [ ] Document the `shared/` package's wikitext processing logic
-   [ ] Consolidate remaining worker Summary dataclasses into `shared_objects.py`
-   [ ] Add proper DB session rollback handling

## Improvement Plan

### Quick Wins

1. Add `/healthz` endpoint for monitoring
2. Create proper error templates (404.html, 500.html)
3. Fix the Fernet thread-safety lock

### Medium-Term

1. Add request timing middleware
2. Consolidate remaining worker Summary dataclasses
3. Add pytest fixtures for app factory with TestingConfig

### Long-Term

1. Introduce dependency injection for `settings`
2. Migrate job system to Celery
3. Add OpenTelemetry instrumentation

## Comprehensive Review

| Metric                   | Score                                     |
| ------------------------ | ----------------------------------------- |
| **Overall Rating**       | **6.5/10**                                |
| **Production Readiness** | Moderate — functional but fragile         |
| **Technical Debt**       | Moderate — legacy refactoring in progress |
| **Risk Assessment**      | Medium                                    |
| **Maintainability**      | 6/10                                      |
