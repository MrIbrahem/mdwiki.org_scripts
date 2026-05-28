# Analysis: newupdater (Medical Content Updater)

## PHP: `php/newupdater.php`

### Parameters

| Variable | Source  | Type            | Description                  |
| -------- | ------- | --------------- | ---------------------------- |
| `title`  | `$_GET` | text (required) | Page title                   |
| `save`   | `$_GET` | checkbox        | Auto-save toggle (value="1") |

### Flow

1. Renders a GET form with:
    - `title` field (text, required)
    - `save` checkbox (auto-save)
2. On submit with logged-in user:
    - Sanitizes title (replaces spaces and `+`)
    - Calls `do_py_new()` to run `newupdater.py -page:title from_toolforge [save]`
    - Processes result:
        - `"no changes"` → "no changes" message + edit link
        - `"save ok"` → success message
        - `"notext"` → empty text
        - `.txt` filename → renders a pre-filled edit form with the new text
        - Other → displays result as-is

### `generateEditForm()` function

-   Creates a POST form targeting `mdwiki.org/w/index.php` (direct wiki editing)
-   Shows old and new text for comparison

### `do_py_new()` function

-   Runs Python locally instead of Toolforge:
    ```
    python3 path/to/newupdater.py -page:title from_toolforge [save]
    ```

## Python: `python/newupdater.py`

### How it works

1. `work_on_title(title)`:
    - Fetches the current page text
    - Calls `work_on_text(title, text)` from `new_updater` module
    - Compares old vs new text
    - Returns: `"notext"`, `"no changes"`, or new text
2. `work(title)`:
    - If `save` in `sys.argv` → saves page directly, returns `"save ok"`
    - Otherwise → caches new text to file, returns filename
3. `save_cash(title, new_text)`:
    - Writes new text to a file in `updatercash/` directory

### Mapping

| PHP              | Python CLI                                 |
| ---------------- | ------------------------------------------ |
| `$_GET['title']` | `-page:title` (with `_` replaced by space) |
| `$_GET['save']`  | `save` in `sys.argv`                       |

---

## Flask Migration Vision

### Current route: `flask_app/main_app/app_routes/newupdater/__init__.py`

```
GET /newupdater/?title=X&save=1  → process and display result
GET /newupdater/                 → render empty form
```

### Remaining work

1. **Direct `newupdater.py` call**
    - Import `get_new_text()` and `work()` from `newupdater.py`
    - Pass `title` and `save` directly
2. **Pre-filled edit form** — instead of POSTing to mdwiki.org
    - Display diff between old and new text
    - In-app save button
3. **Remove file-based cache** — store results in memory or database
4. **Preview support** — preview before saving
