Here's the plan:

## Plan: Replace `active_coordinators()` calls with `user.is_active_admin`

### Problem

`active_coordinators()` loads **all** active coordinator usernames from DB every time, just to check if one user is admin. With `is_active_admin` on `CurrentUser`, we can populate it once at construction and read it everywhere.

### Step 1 — Add targeted query in `admin_service.py`

Add `is_active_coordinator(username: str) -> bool` that does a single-row lookup:

```python
def is_active_coordinator(username: str) -> bool:
    return db.session.query(AdminUserRecord).filter(
        AdminUserRecord.username == username,
        AdminUserRecord.is_active,
    ).first() is not None
```

Keep `active_coordinators()` — it's still needed for the coordinators dashboard (listing all).

### Step 2 — Populate `is_active_admin` in `users_service.py`

In both `save_and_get_user()` and `get_authenticated_user()`, call the new query and pass the result:

```python
is_active_admin=is_active_coordinator(username),
```

### Step 3 — Replace all single-user admin checks

| File                                | Line  | Current                                      | After                                     |
| ----------------------------------- | ----- | -------------------------------------------- | ----------------------------------------- |
| `routes_utils.py:_is_admin()`       | 15-17 | `user.username in active_coordinators()`     | `getattr(user, "is_active_admin", False)` |
| `routes_utils.py:context_user()`    | 33    | `_is_admin(user)`                            | same function, now reads field            |
| `routes_utils.py:can_run_jobs()`    | 58    | `_is_admin(user)`                            | same                                      |
| `routes_utils.py:can_run_bg_jobs()` | 68    | `_is_admin(user)`                            | same                                      |
| `new_jobs.py:_can_manage_job()`     | 44    | `user.username in active_coordinators()`     | `getattr(user, "is_active_admin", False)` |
| `admins_required.py:admin_required` | 29    | `user.username not in active_coordinators()` | `not user.is_active_admin`                |

After these changes, `routes_utils.py` and `new_jobs.py` no longer need to import `active_coordinators`.

### Step 4 — Remove stale imports

Remove `active_coordinators` from imports in `routes_utils.py` and `new_jobs.py` (keep it in `admin_service/__init__.py` exports and `coordinators.py` route where the full list is displayed).

### Step 5 — Update tests

-   Update `CurrentUser` construction in test fixtures to pass `is_active_admin=True` where admin behavior is tested
-   The `admins_required` tests already mock `active_coordinators` — switch them to set `is_active_admin` on the mock user instead

### Note on staleness

If an admin is deactivated while they have an active session, `is_active_admin` stays `True` until their next login (when `get_authenticated_user` re-queries). This is acceptable — same behavior as the current approach since `active_coordinators()` is also cached per-request.

### No changes needed

-   **Templates** — already use `is_admin` from context processor, which will now derive from `user.is_active_admin`
-   **`coordinators.py` route** — still needs `active_coordinators()` to list all coordinators on the dashboard
-   **`admin_service.py` exports** — `active_coordinators` stays exported
