# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask web application providing batch maintenance tools for [mdwiki.org](https://mdwiki.org) (a medical wiki on Wikimedia infrastructure). Runs on **Wikimedia Toolforge** (Kubernetes). Users authenticate via MediaWiki OAuth and run jobs that modify wiki pages through the MediaWiki API.

## Common Commands

### Development Server

```bash
python src/app1.py          # Development server (loads .env, debug mode)
```

### Testing

```bash
python -m pytest tests/ -v                    # All tests (network tests excluded by default)
python -m pytest tests/ -v -m unit            # Unit tests only
python -m pytest tests/ -v -m integration     # Integration tests only
python -m pytest tests/ -v -m network         # Network tests (requires live API)
python -m pytest tests/unit/test_file.py -v   # Single test file
python -m pytest tests/unit/test_file.py::test_name -v  # Single test
```

### Linting & Formatting

```bash
ruff check src/ tests/      # Lint with Ruff
ruff format src/ tests/     # Format with Ruff
black src/ tests/           # Format with Black
isort src/ tests/           # Sort imports
```

## Architecture

### Application Factory Pattern

`src/main_app/__init__.py` contains `create_app(config_class)` which initializes Flask, registers extensions, blueprints, and database.

### Entry Points

-   `src/app.py` — Production WSGI entry (ProductionConfig)
-   `src/app1.py` — Development entry (DevelopmentConfig, loads `.env`)

### Configuration

Environment-based via frozen dataclasses in `src/main_app/config/`. Settings loaded from env vars into a singleton `settings` object in `main_settings.py`. See `.env.example` for required variables.

### Blueprint Structure

Routes registered in `src/main_app/app_routes/__init__.py`:

-   `bp_main` — Index page
-   `bp_auth` — OAuth login/callback/logout, rate limiting
-   `bp_fixred` — Single-page redirect fixer (`/fixred/`)
-   `bp_public_jobs` — Admin job management (`/public_jobs/`)
-   `bp_newupdater` — Medical content updater (`/newupdater/`)

### Background Job System

Jobs run in daemon threads via `src/main_app/public_jobs/`:

-   `base_worker_object.py` — Abstract `BaseObjectsJobWorker` with lifecycle hooks (`before_run`, `process`, `after_run`)
-   `jobs_worker.py` — Job runner with `start_job()`, `cancel_job()`, threading infrastructure
-   `workers_list.py` — Registry mapping job types to worker classes
-   `workers/` — One subdirectory per job type (e.g., `find_and_replace/`, `create_redirects/`)

### Service Layers

-   `db/services/` — Database CRUD (SQLAlchemy models: `JobRecord`, `UserTokenRecord`, `AdminUserRecord`)
-   `api_services/` — MediaWiki API client layer (mwclient-based, OAuth-authenticated)
-   `su_services/` — Higher-level services (`current_user()`, `oauth_required` decorator)
-   `shared/` — Business logic shared between routes and jobs

### Separation of Concerns

Strict layering enforced — dependency flow is **Controller → Service → Repository → Database**:

-   **Controllers** (`app_routes/`) — Request validation, auth checks, service calls, and responses only. Must never import or call `db/services/` or SQLAlchemy models directly.
-   **Services** (`su_services/`, `shared/`) — Business logic and orchestration. Call repositories for data access, API services for external calls.
-   **Repositories** (`db/services/`) — Data access only. All SQLAlchemy queries and mutations live here. No business logic.
-   Controllers must not contain database queries, model imports, or business rules.
-   Services must not access `request`, `session`, or return Flask responses.

### MediaWiki Integration

-   Uses `mwclient` for API calls, `mwoauth` for OAuth 1.0a handshake
-   OAuth tokens encrypted with Fernet (`cryptography` library) before DB storage
-   Interacts with both `en.wikipedia.org` (data source) and `mdwiki.org` (edit target)

### Database

-   Production: MySQL via PyMySQL on Toolforge ToolsDB
-   Tests: SQLite in-memory (`TestingConfig`)
-   Migrations via Flask-Migrate/Alembic

### Frontend

Jinja2 templates with Bootstrap 5, jQuery, DataTables, and Ace editor. Base layout in `templates/base.html`.

## Code Style

-   **Line length**: 120 characters
-   **Python target**: 3.13
-   **Primary linter/formatter**: Ruff (also Black available)
-   **Import sorting**: isort with Black profile
-   **Type hints**: Used but not enforced (mypy configured with `ignore_missing_imports`)

## Testing Conventions

-   `pytest-socket` blocks network access by default (autouse fixture)
-   Mark network-dependent tests with `@pytest.mark.network`
-   Test fixtures in `tests/conftest.py`: `mock_client` (Flask test client), `login` (session mock), `csrf_tokens`
-   `TestingConfig` uses SQLite in-memory and disables CSRF

## Deployment

Wikimedia Toolforge Kubernetes — see `toolforge_tool/service.template` (python3.13, 2 replicas, 1Gi RAM, 2 CPU). Deployment scripts in `toolforge_tool/shs/`.
