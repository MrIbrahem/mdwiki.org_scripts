# Analysis: redirect (Create Redirects)

## PHP: `php/redirect.php`

### Parameters

| Variable    | Source              | Type     | Description                             |
| ----------- | ------------------- | -------- | --------------------------------------- |
| `title`     | `$_GET` or `$_POST` | text     | Single page title                       |
| `titlelist` | `$_GET` or `$_POST` | textarea | List of titles (alternative to `title`) |

### Flow

1. Renders a POST form with:
    - `title` field (text)
    - OR `titlelist` textarea
2. On submit with logged-in user:
    - **If `title` is populated:**
        - Builds command: `red.py -page2:urlencoded_title save`
    - **If `titlelist` is populated:**
        - Writes list to `redirectlist.txt`
        - Builds command: `red.py -file:path save`
    - Executes via `do_py()`

## Python: `python/red.py`

### How it works

1. For each page calls `work(title, num, length)`:
    - Checks if the page exists on mdwiki
    - Calls `get_red(title)` to fetch redirects from enwiki
    - For each redirect not already on mdwiki:
        - Validates the title (`valid_title`)
        - Creates redirect page `#redirect [[title]]`
2. `get_red(title)`:
    - Queries enwiki API for redirects of a given page
    - Returns titles in namespace 0 only

### Supported CLI args

-   `-page2:title`, `-page:title` — single title
-   `-file:path` — title list file
-   `-newpages:N`, `-user:NAME`, `-start:X`, `-ns:N`, `search:TERM`

### Mapping

| PHP                       | Python CLI                |
| ------------------------- | ------------------------- |
| `$_GET/POST['title']`     | `-page2:urlencoded_title` |
| `$_GET/POST['titlelist']` | `-file:redirectlist.txt`  |

---

## Flask Migration Vision

### Current route: `flask_app/main_app/app_routes/redirect/__init__.py`

```
GET  /redirect/  → render form
POST /redirect/  → accept and process
```

### Remaining work

1. **Direct `red.py` call**
    - Import `work()` and `get_red()` from `red.py`
    - Pass title directly without CLI
2. **File handling** — replace `redirectlist.txt` with direct list passing
3. **Add support for new pages** — `-newpages` and `-usercontribs`
