# utils — Validation Helpers

## Project Overview

Minimal utility module providing input validation for API service functions.

### File: `verify.py`

Single function: `verify_required_fields(required_fields: Dict[str, Any]) -> List[str]`

Returns a list of field names that have falsy values (None, "", 0, False, etc.).

```python
def verify_required_fields(required_fields: Dict[str, Any]) -> List[str]:
    missing_fields = []
    for field, value in required_fields.items():
        if not value:
            logger.error(f"Missing required field: {field}")
            missing_fields.append(field)
    return missing_fields
```

**Usage**: Called by `api_services/pages_api.py` to validate inputs before MediaWiki API calls.

## Testing

```bash
pytest tests/unit/utils --cov=flask_app/main_app/utils
```

## Strengths

-   Simple, focused utility
-   Proper logging of missing fields
-   Used consistently across API service layer

## Weaknesses

-   Logs at ERROR level for what might be expected input validation
-   Could be a single function in a larger utils module
-   No type-specific validation (e.g., checking string format)

## Comprehensive Review

| Metric              | Score                        |
| ------------------- | ---------------------------- |
| **Overall Rating**  | **5/10**                     |
| **Simplicity**      | Good                         |
| **Utility**         | Moderate — only one function |
| **Maintainability** | N/A (too small)              |
