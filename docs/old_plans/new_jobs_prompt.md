write a plan to merge old jobs into new_jobs, while keeping old `jobs` as its for `refernces`

all jobs in `flask_app/main_app/jobs`

-   create_redirects
-   duplicate_redirect
-   find_and_replace
-   fixred_all
-   fixref
-   import_history

should use `flask_app/main_app/new_jobs/jobs_worker.py`

start by creating folder for each job in `flask_app/main_app/new_jobs/workers`:

-   `__init__.py` placeholder:

```python
from __future__ import annotations

from .worker import job_worker_entry

__all__ = [
    "job_worker_entry",
]

```

-   `worker.py` placeholder:

```python
"""
Worker module.

"""

from __future__ import annotations

import mwclient
import logging
import threading
from datetime import datetime
from typing import Any, Dict, Iterable
from ....new_jobs.base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


class JobWorker(BaseJobWorker):
    """Background worker"""

    def __init__(
        self,
        job_id: int,
        args: Any,
        user: dict[str, Any] | None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args
        self.site: mwclient.Site | None = None
        super().__init__(job_id, user, cancel_event)

    # ------------------------------------------------------------------
    # BaseJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "<job_type>"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "checked": 0,
                "to_rename": 0,
                "renamed": 0,
                "skipped_target_exists": 0,
                "redirected": 0,
                "failed": 0,
            },
            "pages_processed": [],
        }

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result["status"] = "failed"
            self.result["error"] = "No authenticated user site available. Please log in via OAuth."
            self.result["failed_at"] = datetime.now().isoformat()
            return self.result

        # job logic here

        # in the end
        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------


def job_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """
    Background worker entry-point.
    """
    logger.info(f"Starting job {job_id}: <jobs label>")
    worker = JobWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "job_worker_entry",
]
```

-   job html templates at `flask_app/templates/new_jobs_templates/`
-   register in `flask_app/main_app/new_jobs/workers_list.py` by adding a `JobData` entry to `jobs_data`
