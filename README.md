# MDWiki Scripts

Flask web application providing batch maintenance tools for [mdwiki.org](https://mdwiki.org), a medical wiki on Wikimedia infrastructure.

## Project Overview

This tool runs on **Wikimedia Toolforge** (Kubernetes) and provides various jobs to maintain and update medical content on MDWiki. Users authenticate via MediaWiki OAuth and can run background jobs that modify wiki pages through the MediaWiki API.

## Features

- **OAuth Authentication**: Secure login using MediaWiki credentials.
- **Background Job System**: Run long-running maintenance tasks in the background.
- **Redirect Fixer**: Tool to fix redirects on one or many pages.
- **Medical Content Updater**: Tools for updating medical information.
- **Admin Management**: Interface for managing and monitoring jobs.

## Architecture

The application follows a strict layering: **Controller → Service → Repository → Database**.

- **Flask App**: Main application framework.
- **Background Jobs**: Managed using a custom worker system in `flask_app/main_app/public_jobs/`.
- **MediaWiki Integration**: Uses `mwclient` and `mwoauth`.
- **Database**: SQLAlchemy for data persistence (MySQL in production, SQLite for tests).

## Getting Started

### Prerequisites

- Python 3.13+
- MariaDB/MySQL (for local development, you can use SQLite)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mdwiki-org-scripts
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Set up environment variables:
   Copy `.env.example` to `.env` and fill in the required values.
   ```bash
   cp .env.example .env
   ```

### Running the Development Server

```bash
python flask_app/app1.py
```

## Testing

Tests are managed with `pytest`. Network access is blocked by default in tests.

```bash
python -m pytest tests/ -v                    # All tests
python -m pytest tests/ -v -m unit            # Unit tests only
python -m pytest tests/ -v -m integration     # Integration tests only
```

## Linting and Formatting

We use `Ruff` for linting and formatting.

```bash
ruff check flask_app/ tests/      # Lint
ruff format flask_app/ tests/     # Format
```

## Deployment

The application is deployed on Wikimedia Toolforge using Kubernetes. Deployment details and templates are located in the `toolforge_tool/` directory.
