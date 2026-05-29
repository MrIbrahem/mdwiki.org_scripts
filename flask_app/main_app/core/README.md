# core — Security Utilities

## Project Overview

Core security utilities providing symmetric encryption for OAuth tokens and a custom test client for cookie-based authentication testing.

### Files

| File         | Purpose                                                                    |
| ------------ | -------------------------------------------------------------------------- |
| `crypto.py`  | Fernet symmetric encryption/decryption for OAuth credentials               |
| `cookies.py` | `CookieHeaderClient` — Flask test client that accepts raw `Cookie` headers |

## crypto.py — Fernet Encryption

Provides `encrypt_value()` and `decrypt_value()` using the `cryptography.Fernet` library. The encryption key is loaded from `settings.oauth.encryption_key` (environment variable `OAUTH_ENCRYPTION_KEY`).

```python
def encrypt_value(value: str) -> bytes:
    """Encrypt a UTF-8 string and return the raw Fernet token bytes."""
    return _require_fernet().encrypt(value.encode("utf-8"))

def decrypt_value(token: bytes) -> str:
    """Decrypt a Fernet token and return the UTF-8 string contents."""
    decrypted = _require_fernet().decrypt(token)
    return decrypted.decode("utf-8")
```

**Design**: Lazy singleton `_fernet` initialized on first use via `_require_fernet()`.

## cookies.py — CookieHeaderClient

Custom Flask test client that parses raw `Cookie` header strings and converts them to individual `set_cookie()` calls. Used for testing authenticated routes.

```python
class CookieHeaderClient(FlaskClient):
    def open(self, *args, **kwargs):
        # Extracts "Cookie" header from request
        # Parses with SimpleCookie
        # Calls set_cookie() for each morsel
```

## Strengths

-   **Fernet encryption** is industry-standard symmetric encryption
-   **Lazy initialization** — key loaded only when needed
-   **Clear error messages** for missing/invalid encryption keys
-   **Test client** enables cookie-based auth testing

## Weaknesses

-   **Thread-safety issue** — `_fernet` singleton initialized without lock (lock commented out)
-   **No key rotation** support in the crypto module itself
-   **Global mutable state** — `_fernet` module-level variable

## Critical Issues

> **Warning**: Race condition in Fernet initialization.

```python
# Line 26-27 — lock is commented out:
# with _fernet_lock:
_fernet = Fernet(key_bytes)
```

Under concurrent requests, multiple threads could initialize `_fernet` simultaneously.

## Areas That Need Attention

-   [ ] Uncomment and implement the thread-safety lock
-   [ ] Add key rotation support
-   [ ] Add unit tests for encrypt/decrypt round-trip

## Improvement Plan

### Quick Wins

1. Re-enable the thread lock for `_fernet` initialization

### Medium-Term

1. Add Fernet key rotation support
2. Add comprehensive unit tests

## Comprehensive Review

| Metric              | Score                     |
| ------------------- | ------------------------- |
| **Overall Rating**  | **6/10**                  |
| **Security**        | Good (Fernet is strong)   |
| **Thread Safety**   | Poor (lock commented out) |
| **Testability**     | Moderate                  |
| **Maintainability** | 7/10                      |
