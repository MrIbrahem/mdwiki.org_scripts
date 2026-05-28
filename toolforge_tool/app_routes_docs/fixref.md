# Analysis: fixref (Normalize References)

## PHP: `php/fixref.php`

### Parameters

| Variable    | Source              | Type     | Description                               |
| ----------- | ------------------- | -------- | ----------------------------------------- |
| `titlelist` | `$_GET` or `$_POST` | textarea | List of titles (one per line)             |
| `number`    | `$_GET` or `$_POST` | number   | Number of pages to process (for allpages) |

### Flow

1. Renders a POST form with:
    - `number` field (page count)
    - OR `titlelist` (textarea for title list)
2. On submit with logged-in user:
    - **If `titlelist` is populated:**
        - Single line → `-title:escaped_title`
        - Multiple lines → writes to temp file, uses `-file:path`
    - **If `number` is populated:** → `allpages -number:N`
    - Executes via `do_py()`: `fixref/start.py command save`

## Python: `python/fixref/start.py`

### How it works

1. Reads CLI args:
    - `-number:N` — page count
    - `-file:path` — file with title list
    - `allpages` — all pages
    - `-cat:Category` — category page
    - `-page:title` or `-title:title` — single title
2. For each page:
    - Fetches the page text
    - Calls `fix_ref_template()` to normalize references
    - If text changed → saves the page
3. Max limit: `thenumbers[1]` (default 20000)

### Mapping

| PHP                                     | Python CLI             |
| --------------------------------------- | ---------------------- |
| `$_GET/POST['titlelist']` (single line) | `-title:escaped_title` |
| `$_GET/POST['titlelist']` (multiple)    | `-file:temp_file_path` |
| `$_GET/POST['number']`                  | `allpages -number:N`   |

---

## Flask Migration Vision

### Current route: `flask_app/main_app/app_routes/fixref/__init__.py`

```
GET  /fixref/  → render form
POST /fixref/  → accept and process
```

### Remaining work

1. **Direct `fixref/start.py` call**
    - Import `work()` from `start.py`
    - Decouple title list building from `sys.argv`
2. **Temp file handling** — pass list directly instead of writing files
3. **Category support (`-cat`)** — add optional field to the form
