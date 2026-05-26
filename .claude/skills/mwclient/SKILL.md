---
name: mwclient
description: |
    Python client for the MediaWiki API. Provides a high-level interface for
    interacting with wikis (like Wikipedia). Core abstractions: Site (connection),
    Page (wiki pages), and Image (files).

    Covers: connecting to wikis, reading/editing pages, uploading files, querying
    lists, authentication (OAuth, login), and error handling.

    Use when: automating wiki edits, scraping wiki content, uploading files,
    or building bots for MediaWiki instances.
user-invocable: true
---

# mwclient

Python client for the MediaWiki API.

## Installation

```bash
pip install mwclient
```

## Quick Start

```python
import mwclient

# Connect to a wiki
site = mwclient.Site('en.wikipedia.org')

# Read a page
page = site.pages['Python (programming language)']
print(page.text())

# Edit a page (requires login)
site.login('username', 'password')
page.edit('New content', summary='Updated via mwclient')
```

## References

| Reference                        | Description                                             |
| -------------------------------- | ------------------------------------------------------- |
| [site](references/site.md)       | Site connection, authentication, and site-level queries |
| [page](references/page.md)       | Page operations: read, edit, move, delete, listings     |
| [images](references/images.md)   | File/image operations: download, upload, metadata       |
| [listing](references/listing.md) | Pagination and iteration over API results               |
| [errors](references/errors.md)   | Exception handling and error types                      |

## Core Concepts

### Site

The `Site` class is the entry point. It manages the HTTP session, handles authentication, and provides access to pages.

### Page

The `Page` class represents a wiki page. Use it to read content, make edits, and query page relationships (links, categories, backlinks).

### Image

The `Image` class (subclass of `Page`) handles file operations. Use it to download files or check file usage.

### Listings

All listing methods return lazy iterators that fetch data in chunks. Use `max_items` to limit results and `api_chunk_size` to control chunk size.

## Common Patterns

### Connect with authentication

```python
site = mwclient.Site('mywiki.org')
site.clientlogin(username='bot', password='secret')
```

### Read and edit

```python
page = site.pages['Target Page']
text = page.text()
page.edit(text + '\nNew line', summary='Added line')
```

### Iterate search results

```python
for page in site.search('python', namespace=0, max_items=10):
    print(page.name)
```

### Upload a file

```python
with open('image.png', 'rb') as f:
    site.upload(f, filename='image.png', description='My image')
```

## Error Handling

Catch `mwclient.errors.MwClientError` for all library errors, or specific exceptions:

```python
from mwclient import errors

try:
    page.edit('content')
except errors.ProtectedPageError:
    print('Page is protected')
except errors.AssertUserFailedError:
    print('Not logged in')
```

## Resources

-   Documentation: [ mwclient.readthedocs.io ](https://mwclient.readthedocs.io)
-   Source: [github.com/mwclient/mwclient](https://github.com/mwclient/mwclient)
