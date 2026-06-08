# Plan: Split `user_tokens` into `users` + `user_tokens`

## Problem

`admin_users.username` and `jobs.username` have FK constraints pointing to
`user_tokens.username`. Deleting a user token (logout) fails because MySQL
blocks it:

```
sqlalchemy.exc.IntegrityError: (1451, 'Cannot delete or update a parent row:
a foreign key constraint fails (`mdwiki_scripts`.`admin_users`,
CONSTRAINT `admin_users_ibfk_1` FOREIGN KEY (`username`) REFERENCES
`user_tokens` (`username`))')
```

Removing `db.ForeignKey` from SQLAlchemy models does NOT remove the constraint
from the MySQL database.

## Solution

Create a `users` table as the stable identity layer. All tables reference
`users` instead of `user_tokens`. Token data becomes a child of users.

---

## New Schema

```
users               (NEW)
├── user_id  PK
├── username UNIQUE
├── created_at
└── updated_at

user_tokens          (MODIFIED)
├── user_id  PK, FK → users.user_id ON DELETE CASCADE
├── access_token
├── access_secret
├── created_at
├── updated_at
├── last_used_at
└── rotated_at

admin_users          (MODIFIED)
├── id       PK
├── username FK → users.username ON DELETE CASCADE
├── is_active
├── created_at
└── updated_at

jobs                 (MODIFIED — no FK on username)
├── id       PK
├── job_type
├── username (plain column — no FK, jobs persist independently)
├── status, timestamps, result_file
```

**Key decisions:**

-   `user_tokens.user_id` FK to `users.user_id` with `ON DELETE CASCADE` —
    deleting a user auto-deletes their token
-   `admin_users.username` FK to `users.username` with `ON DELETE CASCADE` —
    deleting a user auto-deletes their admin record
-   `jobs.username` — **no FK** (jobs persist independently; a user can be
    deleted while their jobs remain for audit history)
-   `user_tokens.username` column is **dropped** (username now lives in `users`)

---

## Migration SQL (run on Toolforge MySQL)

```sql
-- 1. Create users table
CREATE TABLE users (
    user_id    INT NOT NULL,
    username   VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 2. Migrate data from user_tokens → users
INSERT INTO users (user_id, username, created_at)
SELECT user_id, username, created_at FROM user_tokens;

-- 5. Add new FK from admin_users → users
ALTER TABLE admin_users
  ADD CONSTRAINT admin_users_ibfk_1
  FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE;

-- 6. Add new FK from user_tokens → users
ALTER TABLE user_tokens
  ADD CONSTRAINT user_tokens_ibfk_1
  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE;

```

---

## Code Changes

### Tier 1 — Models

#### `db/models/users.py`

**Add `UsersRecord`:**

```python
class UsersRecord(db.Model):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime, nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
```

**Modify `UserTokenRecord`:**

```python
class UserTokenRecord(db.Model):
    __tablename__ = "user_tokens"

    user_id = Column(Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    # REMOVE: username column
    access_token = Column(LargeBinary(1024), nullable=False)
    access_secret = Column(LargeBinary(1024), nullable=False)
    # ... timestamps unchanged

    user = db.relationship("UsersRecord", backref=db.backref("token", uselist=False))
```

**Modify `AdminUserRecord`:**

```python
class AdminUserRecord(db.Model):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(
        String(255), db.ForeignKey("users.username", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    # ... rest unchanged
```

**`JobRecord` — no change** (username stays a plain column, no FK).

#### `db/models/__init__.py`

```python
from .users import AdminUserRecord, UsersRecord, UserTokenRecord

__all__ = [
    "AdminUserRecord",
    "UsersRecord",
    "UserTokenRecord",
]
```

---

### Tier 2 — Composite type for `g._current_user`

#### `su_services/current_user.py` (NEW)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CurrentUser:
    """Composite user identity + credentials for request handling."""
    user_id: int
    username: str
    access_token: bytes
    access_secret: bytes

    def to_auth_payload(self) -> dict:
        return {
            "id": self.user_id,
            "username": self.username,
            "access_token": self.access_token,
            "access_secret": self.access_secret,
        }
```

**Why:** All existing code that reads `user.username`, `user.user_id`,
`user.access_token`, `user.access_secret` continues to work unchanged.
No callers need to be modified for attribute access.

---

### Tier 3 — Services

#### `db/services/user_token_service.py`

**Add user CRUD:**

```python
def create_user(user_id: int, username: str) -> UsersRecord:
    """Create a user identity row. Idempotent — returns existing if present."""
    existing = db.session.query(UsersRecord).filter(UsersRecord.user_id == user_id).first()
    if existing:
        if existing.username != username:
            existing.username = username
            db.session.commit()
            db.session.refresh(existing)
        return existing
    record = UsersRecord(user_id=user_id, username=username)
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record

def get_user(user_id: int) -> UsersRecord | None:
    return db.session.query(UsersRecord).filter(UsersRecord.user_id == user_id).first()

def get_user_by_username(username: str) -> UsersRecord | None:
    return db.session.query(UsersRecord).filter(UsersRecord.username == username).first()

def delete_user(user_id: int) -> bool:
    """Delete user + cascading token + admin record."""
    affected = db.session.query(UsersRecord).filter(UsersRecord.user_id == user_id).delete()
    db.session.commit()
    return affected > 0
```

**Modify `upsert_user_token`:**

```python
def upsert_user_token(
    *, user_id: int, username: str, access_key: str, access_secret: str
) -> None:
    # Ensure user row exists first
    create_user(user_id, username)

    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)

    orm_obj = db.session.query(UserTokenRecord).filter(
        UserTokenRecord.user_id == user_id
    ).first()

    if orm_obj:
        orm_obj.access_token = encrypted_token
        orm_obj.access_secret = encrypted_secret
    else:
        orm_obj = UserTokenRecord(
            user_id=user_id,
            access_token=encrypted_token,
            access_secret=encrypted_secret,
        )
        db.session.add(orm_obj)

    db.session.commit()
```

**Modify `delete_user_token`:**

```python
def delete_user_token(user_id: int) -> bool:
    """Delete token only (user identity persists for job history)."""
    affected = db.session.query(UserTokenRecord).filter(
        UserTokenRecord.user_id == user_id
    ).delete()
    db.session.commit()
    return affected > 0
```

**Modify `get_user_token_by_username`:**

```python
def get_user_token_by_username(username: str) -> UserTokenRecord | None:
    user = db.session.query(UsersRecord).filter(UsersRecord.username == username).first()
    if not user:
        return None
    return db.session.query(UserTokenRecord).filter(
        UserTokenRecord.user_id == user.user_id
    ).first()
```

**Modify `list_users`:**

```python
def list_users() -> list[UsersRecord]:
    return db.session.query(UsersRecord).all()
```

#### `db/services/__init__.py`

```python
from .user_token_service import (
    create_user,
    delete_user,
    delete_user_token,
    get_user,
    get_user_by_username,
    get_user_token,
    get_user_token_by_username,
    list_users,
    upsert_user_token,
)
```

#### `su_services/users_service.py`

```python
from .current_user import CurrentUser

class UserService:
    @staticmethod
    def save_and_get_user(
        user_id: int, username: str, access_key: str, access_secret: str
    ) -> CurrentUser | None:
        try:
            upsert_user_token(
                user_id=user_id, username=username,
                access_key=access_key, access_secret=access_secret,
            )
            token = get_user_token(user_id)
            if not token:
                return None
            return CurrentUser(
                user_id=user_id,
                username=username,
                access_token=token.access_token,
                access_secret=token.access_secret,
            )
        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

    @staticmethod
    def get_authenticated_user(user_id: int) -> CurrentUser | None:
        try:
            token = get_user_token(user_id)
            if not token:
                return None
            user = get_user(user_id)
            if not user:
                return None
            return CurrentUser(
                user_id=user_id,
                username=user.username,
                access_token=token.access_token,
                access_secret=token.access_secret,
            )
        except Exception as e:
            logger.error("Error loading user for ID %s: %s", user_id, e)
            return None
```

#### `su_services/auth_service.py`

No changes needed — it already calls `UserService.save_and_get_user()`.

---

### Tier 4 — Routes (minimal changes)

Since `CurrentUser` exposes the same attributes as before, most routes
need **zero changes**. The only file that changes:

#### `app_routes/auth/utils.py`

```python
# load_logged_in_user() — g._current_user is now CurrentUser
# user.username still works, user.user_id still works
# No change needed if CurrentUser has same attribute names
```

#### `app_routes/utils/routes_utils.py`

```python
def load_auth_payload(user) -> Dict[str, Any]:
    if user:
        return user.to_auth_payload()  # use helper method
    return {}
```

---

### Tier 5 — Shared (type hints only)

#### `shared/fixred_one.py`, `shared/newupdater_service.py`

```python
# Change type hint from UserTokenRecord to CurrentUser
from ..su_services.current_user import CurrentUser

def work_on_title(
    title: str,
    save: bool = False,
    summary: str = "Med updater.",
    user: CurrentUser | None = None,
) -> ...:
```

`user.access_token` and `user.access_secret` still work on `CurrentUser`.

---

### Tier 6 — Tests

| File                                                      | Change                                                                          |
| --------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `tests/unit/db/models/test_users.py`                      | Add `UsersRecord` tests; update `UserTokenRecord` constructor (no username)     |
| `tests/unit/db/services/test_user_token_service.py`       | Test `create_user`, `get_user`, `delete_user`; update `upsert_user_token` tests |
| `tests/unit/app_routes/utils/test_routes_utils.py`        | Mock `CurrentUser` instead of `UserTokenRecord`                                 |
| `tests/unit/app_routes/newupdater/test_route.py`          | Construct `CurrentUser` instead of `UserTokenRecord`                            |
| `tests/unit/app_routes/auth/test_auth_utils.py`           | Mock returns `CurrentUser`                                                      |
| `tests/unit/app_routes/test_public_jobs.py`                  | Mock `user.username` — still works on `CurrentUser`                             |
| `tests/unit/app_routes/admin/test_admins_required.py`     | Mock `user.username` — still works                                              |
| `tests/integration/app_routes/auth/test_auth_routes.py`   | `get_user_token` returns `UserTokenRecord` (no username); assert via `get_user` |
| `tests/integration/app_routes/test_jobs_routes.py`        | `upsert_user_token` still works (auto-creates user)                             |
| `tests/integration/app_routes/admin/test_admin_routes.py` | `upsert_user_token` still works                                                 |

---

## File Change Summary

| #   | File                                | Change Type                                                              |
| --- | ----------------------------------- | ------------------------------------------------------------------------ |
| 1   | `db/models/users.py`                | Add `UsersRecord`, modify `UserTokenRecord`, update `AdminUserRecord` FK |
| 2   | `db/models/__init__.py`             | Export `UsersRecord`                                                     |
| 3   | `su_services/current_user.py`       | **NEW** — `CurrentUser` dataclass                                        |
| 4   | `db/services/user_token_service.py` | Add user CRUD, modify token functions                                    |
| 5   | `db/services/__init__.py`           | Export new functions                                                     |
| 6   | `su_services/users_service.py`      | Return `CurrentUser`, call `create_user`                                 |
| 7   | `su_services/__init__.py`           | Export `CurrentUser`                                                     |
| 8   | `app_routes/utils/routes_utils.py`  | Use `to_auth_payload()`                                                  |
| 9   | `shared/fixred_one.py`              | Type hint → `CurrentUser`                                                |
| 10  | `shared/newupdater_service.py`      | Type hint → `CurrentUser`                                                |
| 11  | `db/models/jobs.py`                 | Update docstring                                                         |
| 12  | `db/services/admin_service.py`      | Update error message string                                              |
| 13  | Tests (10+ files)                   | Update constructors, mocks, assertions                                   |

**Files that need NO changes:** `auth/routes.py`, `auth/utils.py`, `auth/cookie.py`,
`auth/oauth.py`, `admin/admins_required.py`, `public_jobs.py`, `profile.py`,
`api_services/clients/wiki_client.py`, `extensions.py`, all workers.

---

## Execution Order

1. Save migration SQL → `toolforge_tool/migrations/001_split_user_tokens.sql`
2. Run migration SQL on Toolforge MySQL
3. Apply code changes (Tier 1 → Tier 6)
4. Run `ruff check` + `ruff format`
5. Run `python -m pytest tests/ -v`
6. Deploy to Toolforge
