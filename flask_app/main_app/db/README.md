# db — Database Layer

## Project Overview

SQLAlchemy-based database layer providing ORM models and CRUD service functions. Uses Flask-SQLAlchemy with MySQL (production) and SQLite (testing).

### Structure

```
db/
├── __init__.py           # init_db() — auto-creates tables + views on startup
├── exceptions.py         # MaxUserConnectionsError, InsufficientDatabaseConfigError
├── models/
│   ├── __init__.py       # Re-exports all models
│   ├── users.py          # AdminUserRecord, UserTokenRecord
│   └── jobs.py           # JobRecord
└── services/
    ├── __init__.py       # Re-exports all service functions
    ├── user_token_service.py  # OAuth token CRUD
    └── jobs_service.py        # Job lifecycle management
```

### Models

#### `UserTokenRecord`

Stores encrypted OAuth credentials for authenticated MediaWiki users.

| Column          | Type                | Notes                              |
| --------------- | ------------------- | ---------------------------------- |
| `user_id`       | Integer (PK)        | MediaWiki user ID                  |
| `username`      | String(255), unique | MediaWiki username                 |
| `access_token`  | LargeBinary(1024)   | Fernet-encrypted OAuth token       |
| `access_secret` | LargeBinary(1024)   | Fernet-encrypted OAuth secret      |
| `created_at`    | DateTime            | Server-default `CURRENT_TIMESTAMP` |
| `updated_at`    | DateTime            | Auto-updated on change             |
| `last_used_at`  | DateTime            | Last authentication                |
| `rotated_at`    | DateTime            | Last token rotation                |

Methods: `decrypted()` → `(access_key, access_secret)` tuple

#### `AdminUserRecord`

Admin users table for authorization.

| Column                      | Type                  | Notes      |
| --------------------------- | --------------------- | ---------- |
| `id`                        | Integer (PK, auto)    |            |
| `username`                  | String(255), unique   |            |
| `is_active`                 | Boolean, default True |            |
| `created_at` / `updated_at` | DateTime              | Timestamps |

#### `JobRecord`

Background job tracking.

| Column                      | Type                          | Notes                                      |
| --------------------------- | ----------------------------- | ------------------------------------------ |
| `id`                        | Integer (PK, auto)            |                                            |
| `job_type`                  | String(255)                   | Worker type identifier                     |
| `username`                  | String(255), nullable         | Job owner                                  |
| `status`                    | String(50), default "pending" | pending/running/completed/failed/cancelled |
| `started_at`                | DateTime, nullable            |                                            |
| `completed_at`              | DateTime, nullable            |                                            |
| `result_file`               | String(500), nullable         | JSON result filename                       |
| `created_at` / `updated_at` | DateTime                      | Timestamps                                 |

### Services

#### `user_token_service.py`

-   `upsert_user_token(user_id, username, access_key, access_secret)` — Insert or update encrypted tokens
-   `get_user_token(user_id)` → `Optional[UserTokenRecord]`
-   `get_user_token_by_username(username)` → `Optional[UserTokenRecord]`
-   `delete_user_token(user_id)`

#### `jobs_service.py`

-   `create_job(job_type, username)` → `JobRecord`
-   `get_job(job_id, job_type)` → `JobRecord` (raises `LookupError`)
-   `list_jobs(limit, job_type)` → `list[JobRecord]`
-   `update_job_status(job_id, status, result_file, job_type)` → `JobRecord`
-   `cancel_job(job_id, job_type)` → `bool`
-   `is_job_cancelled(job_id, job_type)` → `bool`
-   `delete_job(job_id, job_type)` → `bool`

### Database Initialization (`__init__.py`)

```python
def init_db(app, _db):
    # Create real tables (skip views)
    real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
    _db.metadata.create_all(_db.engine, tables=real_tables, checkfirst=True)
    # Create views manually from SQL in __table_args__["info"]
```

Idempotent — safe to call on every startup.

## Testing

```bash
pytest tests/unit/db --cov=flask_app/main_app/db
```

## Strengths

-   **Clean model definitions** with proper server defaults
-   **Encrypted token storage** via `@validates` decorator
-   **Idempotent initialization** — safe for repeated startup
-   **Service functions** are module-level (not classes) — simple and direct
-   **Proper `LookupError`** raised for missing records

## Weaknesses

-   **No session rollback** handling in service functions
-   **`is_job_cancelled()`** calls `db.session.refresh()` on every check — performance concern
-   **No connection pooling** configuration beyond defaults
-   **`delete_user_token`** doesn't check if record exists first
-   **No soft-delete** support for jobs
-   **No pagination** for `list_jobs` (uses `LIMIT` only)

## Critical Issues

> **Warning**: Missing rollback handling can leave the session in an inconsistent state.

```python
# Current pattern (no rollback):
db.session.add(job)
db.session.commit()  # If this fails, session is broken

# Recommended pattern:
try:
    db.session.add(job)
    db.session.commit()
except Exception:
    db.session.rollback()
    raise
```

## Areas That Need Attention

-   [ ] Add try/except rollback blocks to all service functions
-   [ ] Optimize `is_job_cancelled()` — use a lightweight query instead of `refresh()`
-   [ ] Add pagination to `list_jobs()`
-   [ ] Add database migration scripts (Alembic)
-   [ ] Add indexes for common query patterns

## Improvement Plan

### Quick Wins

1. Add rollback handling to all service functions
2. Add index on `jobs.status + jobs.created_at` (already exists per model comment)

### Medium-Term

1. Optimize `is_job_cancelled()` with a lightweight SELECT
2. Add pagination support
3. Add Alembic migration scripts

### Long-Term

1. Add soft-delete for jobs
2. Add audit logging for token operations

## Comprehensive Review

| Metric                   | Score                     |
| ------------------------ | ------------------------- |
| **Overall Rating**       | **6.5/10**                |
| **Production Readiness** | Moderate                  |
| **Technical Debt**       | Low-Moderate              |
| **Risk Assessment**      | Medium (missing rollback) |
| **Maintainability**      | 7/10                      |
