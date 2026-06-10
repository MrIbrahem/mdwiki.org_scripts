from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class JobData:
    job_type: str
    job_name: str
    job_list_template: str

    job_callable: Callable
    job_args: list | None = None
    start_confirm_message: str | None = None
    job_details_template: Optional[str] = "jobs_templates/_help_templates/shared_details.html"
    ready: bool = False
