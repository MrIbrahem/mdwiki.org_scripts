# su_services — User Auth & File Services

## Project Overview

Service layer for user authentication state management and job result file persistence. Bridges the auth system with route handlers and the background job system.

### Structure

```
su_services/
├── __init__.py           # Re-exports: CurrentUser, current_user, oauth_required, save/load_job_result
├── users_service.py      # CurrentUser dataclass, current_user(), oauth_required decorator
└── jobs_files_service.py # Job result file I/O (JSON persistence)
```

## Key Components

### users_service.py — Authentication

#### `CurrentUser` (dataclass)

Lightweight representation of the authenticated user:

```python
@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    username: str
```

#### `current_user()` → `Optional[UserTokenRecord]`

Resolves the current authenticated user through a fallback chain:

1. Check `g._current_user` cache (request-scoped)
2. Check Flask session for `uid`
3. Check signed cookie (`uid_enc`) via `extract_user_id()`
4. Query database for `UserTokenRecord`

Caches result in `g._current_user` for request lifetime.

#### `oauth_required` (decorator)

Redirects unauthenticated users to login:

```python
@oauth_required
def protected_route():
    # current_user() is guaranteed non-None here
```

Saves `request.url` as `post_login_redirect` in session for post-login redirect.

### jobs_files_service.py — File I/O

| Function                                  | Description                              |
| ----------------------------------------- | ---------------------------------------- |
| `get_jobs_data_dir()`                     | `@lru_cache` path to `MAIN_DIR/new_jobs` |
| `save_job_result(job_id, data)`           | Saves JSON to `job_{id}.json`            |
| `save_job_result_by_name(filename, data)` | Saves JSON with custom filename          |
| `load_job_result(result_file)`            | Loads JSON from jobs directory           |

JSON serialization uses `default=str` for datetime handling.

## Testing

```bash
pytest tests/unit/su_services --cov=flask_app/main_app/su_services
```

## Strengths

-   **Clean decorator pattern** for auth (`oauth_required`)
-   **Proper caching** in Flask `g` object — no redundant DB queries per request
-   **Fallback chain** — g → session → cookie for user resolution
-   **`frozen=True`** on `CurrentUser` prevents mutation
-   **`@lru_cache`** on `get_jobs_data_dir()` avoids repeated directory lookups

## Weaknesses

-   **Returns ORM object** — `current_user()` returns `UserTokenRecord`, coupling routes to DB model
-   **No token refresh** — if OAuth tokens expire, user appears authenticated but API calls fail
-   **No path validation** in `load_job_result` — potential traversal
-   **`os.path.exists`** used instead of `Path.exists()`
-   **`get_jobs_data_dir` is `@lru_cache`** — can't change path at runtime

## Critical Issues

> **Warning**: No OAuth token expiration handling.

`current_user()` returns a `UserTokenRecord` even if the stored tokens have expired. Routes that call MediaWiki APIs will fail silently or with cryptic errors.

## Areas That Need Attention

-   [ ] Add OAuth token expiration detection
-   [ ] Add path sanitization in `load_job_result`
-   [ ] Return a lightweight DTO instead of ORM object from `current_user()`
-   [ ] Add token refresh mechanism

## Improvement Plan

### Quick Wins

1. Add path validation in `load_job_result`
2. Use `Path.exists()` consistently

### Medium-Term

1. Return a `CurrentUser` DTO instead of `UserTokenRecord`
2. Add token expiration detection

### Long-Term

1. Implement OAuth token refresh flow
2. Add session invalidation on token expiration

## Comprehensive Review

| Metric                   | Score                                   |
| ------------------------ | --------------------------------------- |
| **Overall Rating**       | **6/10**                                |
| **Production Readiness** | Moderate                                |
| **Security**             | Good (signed cookies, encrypted tokens) |
| **Token Management**     | Poor (no refresh/expiration)            |
| **Maintainability**      | 7/10                                    |
