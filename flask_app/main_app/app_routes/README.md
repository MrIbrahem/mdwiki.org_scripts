# app_routes — Flask Route Handlers

## Project Overview

Flask Blueprint-based route handlers implementing the web interface for MDWiki tools. 5 blueprints handle authentication, job management, content updating, and redirect fixing.

### Structure

```
app_routes/
├── __init__.py           # register_blueprints()
├── fixred.py             # bp_fixred — single-page redirect fixer
├── new_jobs.py           # bp_public_jobs — job management dashboard
├── auth/
│   ├── __init__.py
│   ├── routes.py         # bp_auth — OAuth login/logout/callback
│   ├── oauth.py          # OAuth handshake helpers
│   ├── cookie.py         # Signed cookie + state token helpers
│   └── rate_limit.py     # In-memory RateLimiter class
├── main/
│   └── __init__.py       # bp_main — index page
├── newupdater/
│   ├── __init__.py
│   ├── route.py          # bp_newupdater — medical content updater
│   └── worker.py         # UpdaterTextOutcome + work_on_title()
└── utils/
    ├── __init__.py
    └── routes_utils.py   # load_auth_payload(), get_job_detail_url()
```

## Blueprint Routes

### Auth (`bp_auth`)

| Method | Path        | Description                                                    |
| ------ | ----------- | -------------------------------------------------------------- |
| GET    | `/login`    | Initiates MediaWiki OAuth (rate-limited: 5/min)                |
| GET    | `/callback` | OAuth callback, stores encrypted tokens (rate-limited: 10/min) |
| GET    | `/logout`   | Clears session, deletes tokens, clears cookie                  |

**OAuth Flow**:

1. Generate `state_nonce` → sign with `itsdangerous` → store in session
2. Redirect to MediaWiki OAuth authorization
3. Callback: verify state token → complete handshake → encrypt + store tokens → set signed cookie

### Jobs (`bp_public_jobs`, prefix: `/new_jobs`)

| Method | Path                           | Description                      |
| ------ | ------------------------------ | -------------------------------- |
| GET    | `/list`                        | All jobs list                    |
| GET    | `/<job_type>`                  | Jobs filtered by type            |
| GET    | `/<job_type>/<job_id>`         | Job detail with result data      |
| POST   | `/<job_type>/start`            | Start background job             |
| POST   | `/<job_type>/start_with_args`  | Start job with form arguments    |
| POST   | `/<job_type>/<job_id>/cancel`  | Cancel running job (owner check) |
| POST   | `/<job_type>/<job_id>/delete`  | Delete job                       |
| GET    | `/read-job-result-file/<path>` | Serve job result JSON            |

### Newupdater (`bp_newupdater`, prefix: `/newupdater`)

| Method | Path | Description                                          |
| ------ | ---- | ---------------------------------------------------- |
| GET    | `/`  | Synchronous medical content updater (requires OAuth) |

Runs `work_on_title()` inline — fast single-page template normalization.

### Fixred (`bp_fixred`, prefix: `/fixred`)

| Method | Path | Description                                 |
| ------ | ---- | ------------------------------------------- |
| GET    | `/`  | Form to fix redirects in a single page      |
| POST   | `/`  | Processes the redirect fix (requires OAuth) |

### Main (`bp_main`)

| Method | Path           | Description |
| ------ | -------------- | ----------- |
| GET    | `/`            | Index page  |
| GET    | `/favicon.ico` | Favicon     |

## Testing

```bash
pytest tests/unit/app_routes
pytest tests/integration/app_routes

# with coverage
pytest tests/integration/app_routes tests/unit/app_routes --cov=flask_app/main_app/app_routes
```

## Strengths

-   **Clean Blueprint separation** by concern
-   **Proper OAuth state validation** with signed tokens
-   **Rate limiting** on auth endpoints (thread-safe `RateLimiter`)
-   **Owner-based authorization** for job operations (`_can_manage_job`)
-   **`post_login_redirect`** preserves original destination after login
-   **Signed cookies** via `itsdangerous.URLSafeTimedSerializer`

## Weaknesses

-   **`JobsPublicRoutes` class pattern** is unusual — standard decorators are more Pythonic
-   **Duplicate flash messages** in logout handler
-   **`g` object writes** after `make_response()` in logout have no effect
-   **No pagination** for job lists
-   **No input sanitization** on form inputs passed to workers

## Critical Issues

> **Warning**: Security concerns in job routes.

### 1. Missing Authorization on Delete

```python
# Line 259 — @admin_required is commented out
# @admin_required
@bp_public_jobs.post("/<string:job_type>/<int:job_id>/delete")
def delete_job(job_type, job_id):
```

### 2. Potential Path Traversal

```python
# Line 265-268
@bp_public_jobs.get("/read-job-result-file/<path:result_file>")
def read_job_result_file(result_file):
    result_data = load_job_result(result_file)  # No path sanitization
```

### 3. Stale `g` Object Writes in Logout

```python
# After make_response(), these don't affect the response:
g.current_user = None
g.is_authenticated = False
```

## Areas That Need Attention

-   [ ] Restore `@admin_required` on delete endpoint
-   [ ] Add path validation for job result files
-   [ ] Fix `g` object writes in logout (move before `make_response`)
-   [ ] Remove duplicate flash messages in logout
-   [ ] Add pagination for job lists
-   [ ] Add input validation for form data

## Improvement Plan

### Quick Wins

1. Restore authorization on delete endpoint
2. Add path validation for result files
3. Fix logout `g` writes

### Medium-Term

1. Add pagination for job lists
2. Add input validation middleware
3. Convert `JobsPublicRoutes` class to standard route functions

### Long-Term

1. Add API versioning for JSON endpoints
2. Add OpenAPI/Swagger documentation

## Comprehensive Review

| Metric                   | Score                         |
| ------------------------ | ----------------------------- |
| **Overall Rating**       | **6/10**                      |
| **Production Readiness** | Moderate                      |
| **Security**             | 5/10 (missing auth on delete) |
| **API Design**           | Good                          |
| **Maintainability**      | 6/10                          |
