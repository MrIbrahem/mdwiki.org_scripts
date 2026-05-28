# Analysis: import-history (Import History from enwiki)

## PHP: `php/import-history.php`

### Parameters

| Variable    | Source              | Type     | Description                                   |
| ----------- | ------------------- | -------- | --------------------------------------------- |
| `from`      | `$_GET` or `$_POST` | text     | Source language (optional, only with `title`) |
| `title`     | `$_GET` or `$_POST` | text     | Single page title                             |
| `titlelist` | `$_GET` or `$_POST` | textarea | List of titles (alternative to `title`)       |

### Authorization

-   Authorized users only: `Doc James`, `Mr. Ibrahem`
-   Unauthorized users see "Access denied"

### Flow

1. Renders a POST form with:
    - `title` field OR `titlelist` textarea
    - Optional `from` field (source language)
2. On submit with authorized user:
    - **If `title` is populated:**
        - Builds command: `imp.py -page:urlencoded_title -from:urlencoded_from save`
    - **If `titlelist` is populated:**
        - Writes list to `importlist.txt`
        - Builds command: `imp.py -file:path save`
    - Executes via `do_py()`

## Python: `python/imp.py`

### How it works

1. Imports page history from `family="wikipedia"` to `family="mdwiki"`
2. On successful import (>0 revisions):
    - Re-saves the page to restore text after import
    - If save fails → saves to `User:Mr._Ibrahem/title`
3. Supported CLI args:
    - `-page:title`, `-page2:title` — single title
    - `-file:path` — title list file
    - `-from:LANG` — source language
    - `-newpages:N`, `-user:NAME`, `-start:X`, `-ns:N`, `search:TERM`
    - `-offset:N`, `-limit:N`

### Mapping

| PHP                       | Python CLI               |
| ------------------------- | ------------------------ |
| `$_GET/POST['title']`     | `-page:urlencoded_title` |
| `$_GET/POST['from']`      | `-from:urlencoded_value` |
| `$_GET/POST['titlelist']` | `-file:importlist.txt`   |

---

## Flask Migration Vision

### Current route: `flask_app/main_app/app_routes/import_history/__init__.py`

```
GET  /import-history/  → render form
POST /import-history/  → accept and process
```

### Remaining work

1. **Direct `imp.py` call**
    - Import `work()` from `imp.py`
    - Decouple page list building from `sys.argv`
2. **Authorization system** — integrate with Flask-Login and user roles
3. **Support `from`** — add source language field with dropdown
4. **File handling** — replace file writing with direct list passing
