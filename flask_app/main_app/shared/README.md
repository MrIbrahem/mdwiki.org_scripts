# shared — Business Logic & Wikitext Processing

## Project Overview

Shared domain logic for wiki content processing. Contains the medical content updater, redirect fixer, and reference normalizer — the core transformation engines of the application.

### Structure

```
shared/
├── __init__.py           # Empty
├── decode_bytes.py       # coerce_bytes() — type coercion for encrypted values
├── shared_classes.py     # UpdaterTextOutcome — shared result dataclass for single-page operations
├── fixred_one.py         # Single-page redirect fix service
├── fixref_shared/
│   ├── __init__.py
│   ├── fixred_worker.py  # Redirect-fixing algorithm (work_on_text)
│   ├── fixref_text_new.py # Reference normalization (fix_ref_template)
│   └── objects.py        #
│   └── make_title_bot.py # URL → title extraction via Citoid API
└── new_updater/
    ├── __init__.py       # Re-exports work_on_text, FixChembox, etc.
    ├── MedWorkNew.py     # Main entry: work_on_text(title, text)
    ├── chembox.py        # FixChembox — Chembox→Drugbox conversion
    ├── drugbox.py        # TextProcessor — Drugbox normalization
    ├── mv_section.py     # MoveExternalLinksSection
    ├── resources_new.py  # move_resources — extract identifiers
    ├── helps.py          # URL encode/decode
    ├── bots/
    │   ├── expend.py     # Expand abbreviated infobox params
    │   ├── expend_new.py # Expand infobox parameters
    │   ├── old_params.py # Rename deprecated params
    │   └── Remove.py     # portal_remove, remove_cite_web
    └── lists/
        ├── bot_params.py      # Drugbox section parameter definitions
        ├── chem_params.py     # Chembox→Drugbox parameter mapping
        ├── expend_lists.py    # Abbreviation expansion mappings
        └── identifier_params.py # Drug identifier parameter list
```

## Key Components

### shared_classes.py — Shared Result Types

```python
@dataclass(frozen=True)
class UpdaterTextOutcome:
    kind: Literal["notext", "skipped", "changes", "saved"]
    old_text: str = ""
    new_text: str = ""
    newrevid: int = 0
    msg: str = ""
```

Used by single-page operations (`fixred_one.py`, `newupdater/worker.py`) where the caller needs old/new text for diff display.

### fixred_one.py — Single-Page Redirect Fixer

```python
def work_on_title(title, save=False, summary="Fix redirects.") -> UpdaterTextOutcome:
    # Fetch page → run redirect fixer → optionally save
    # Returns: UpdaterTextOutcome(kind="notext"|"skipped"|"changes"|"saved")
```

### fixref_shared/fixred_worker.py — Redirect Algorithm

-   `work_on_text(title, text, site, state)` — Fixes redirect links in page text
-   `RunState` — Caches redirect mappings and normalized titles across pages
-   `_replace_links()` — Replaces `[[old]]` with `[[new|old]]` (preserves display text)
-   Uses batch API calls: `get_page_links()` + `resolve_redirects()`

### fixref_shared/fixref_text_new.py — Reference Normalizer

-   `fix_ref_template(text)` — Normalizes `<ref>` templates
-   `change_lay_source()` — Moves lay source params to `{{lay source}}`
-   `add_title()` — Extracts title from URL via Citoid API when missing

### new_updater/MedWorkNew.py — Medical Content Updater

```python
def work_on_text(title, text):
    # Pipeline: rename_params → move_resources → _drugbox_work → MoveExternalLinksSection
    newtext = old_params.rename_params(newtext)
    newtext = move_resources(newtext, title)
    newtext = _drugbox_work(newtext)
    newtext = MoveExternalLinksSection(newtext).make_new_txt()
    return newtext
```

### new_updater/drugbox.py — Drugbox Processor

`TextProcessor` class normalizes `{{Infobox drug}}` / `{{Drugbox}}` templates:

-   Reorganizes parameters into sections (Names, Clinical data, Legal data, etc.)
-   Handles combo types (mab, vaccine, combo)
-   Creates properly sectioned output with HTML comment markers

### new_updater/chembox.py — Chembox Converter

`FixChembox` converts `{{Chembox}}` templates to `{{Drugbox}}` format using parameter mapping.

### new_updater/resources_new.py — Identifier Extraction

`move_resources()` extracts drug identifiers from infobox into `{{drug resources}}` template.

## Testing

```bash
pytest tests/unit/shared --cov=flask_app/main_app/shared
```

## Strengths

-   **Rich domain knowledge** encoded in parameter mappings and section definitions
-   **`wikitextparser`** used correctly for template manipulation
-   **Pipeline architecture** — each transformation step is independent
-   **`RunState`** enables efficient redirect caching across multiple pages
-   **Citoid API integration** for automatic title extraction from URLs
-   **Batch API operations** for efficiency

## Weaknesses

-   **Extremely complex** business logic with minimal documentation
-   **Heavy regex usage** for wikitext manipulation — fragile
-   **Arabic comments** without English translations in `resources_new.py`
-   **Module-level mutable state** — `page_identifier_params` in `resources_new.py`
-   **No unit tests** for any transformation logic
-   **Deeply nested conditionals** in `drugbox.py` (6+ levels)
-   **Unbounded cache** — `Title_cash` in `make_title_bot.py`

## Critical Issues

> **Warning**: Thread-safety and correctness concerns.

### 1. Global Mutable State

```python
# resources_new.py line 16
page_identifier_params = {}  # Modified across function calls — NOT thread-safe
```

### 2. Unbounded Cache

```python
# make_title_bot.py line 17
Title_cash = {}  # Grows without limit — memory leak
```

### 3. Fragile Regex Patterns

Complex regex patterns for wikitext parsing are untested and could break on edge cases.

## Areas That Need Attention

-   [ ] Add comprehensive unit tests for all transformation functions
-   [ ] Replace global `page_identifier_params` with function parameters
-   [ ] Add LRU cache with size limit for `Title_cash`
-   [ ] Document the transformation pipeline
-   [ ] Translate Arabic comments to English
-   [ ] Add error boundaries for template parsing failures

## Improvement Plan

### Quick Wins

1. Replace `Title_cash = {}` with `functools.lru_cache`
2. Pass `page_identifier_params` as function parameter instead of global
3. Translate Arabic comments

### Medium-Term

1. Add unit tests for each transformation step
2. Document the pipeline architecture
3. Add error handling for malformed wikitext

### Long-Term

1. Refactor `drugbox.py` to reduce nesting
2. Replace regex-based parsing with `wikitextparser` where possible
3. Add integration tests with real wiki content

## Comprehensive Review

| Metric              | Score                           |
| ------------------- | ------------------------------- |
| **Overall Rating**  | **5/10**                        |
| **Domain Logic**    | Excellent (deep wiki knowledge) |
| **Code Quality**    | Poor (complex, undocumented)    |
| **Thread Safety**   | Poor (global mutable state)     |
| **Testability**     | Poor (no tests)                 |
| **Maintainability** | 4/10                            |
