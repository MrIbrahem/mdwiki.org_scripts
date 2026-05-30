
from dataclasses import dataclass
from typing import Callable, Optional

from .workers.add_r_column.worker import add_r_column_worker_entry
from .workers.add_unlinkedwikibase.worker import add_unlinkedwikibase_worker_entry
from .workers.create_redirects.worker import create_redirects_worker_entry
from .workers.duplicate_redirect.worker import duplicate_redirect_worker_entry
from .workers.find_and_replace.worker import find_and_replace_worker_entry
from .workers.fixred_all.worker import fixred_all_worker_entry
from .workers.fixref.worker import fixref_worker_entry
from .workers.import_history.worker import import_history_worker_entry

@dataclass
class JobData:
    job_type: str
    job_name: str
    job_callable: Callable

    job_list_template: str
    job_details_template: Optional[str] = "jobs_templates/_help_templates/shared_details.html"

jobs_data = {
    "add_r_column" : JobData(
        job_type="add_r_column",
        job_name="Add R column",
        job_details_template="one_page_templates/add_r_column/details.html",
        job_list_template="one_page_templates/add_r_column/list.html",
        job_callable=add_r_column_worker_entry,
    ),
    "add_unlinkedwikibase": JobData(
        job_type="add_unlinkedwikibase",
        job_name="Add unlinkedwikibase tag",
        job_list_template="jobs_templates/add_unlinkedwikibase/list.html",
        job_callable=add_unlinkedwikibase_worker_entry,
    ),
    "create_redirects": JobData(
        job_type="create_redirects",
        job_name="Copy Redirects from Enwiki",
        job_details_template="jobs_templates/create_redirects/details.html",
        job_list_template="jobs_templates/create_redirects/list.html",
        job_callable=create_redirects_worker_entry,
    ),
    "duplicate_redirect": JobData(
        job_type="duplicate_redirect",
        job_name="Fix Duplicate Redirects",
        job_details_template="jobs_templates/duplicate_redirect/details.html",
        job_list_template="jobs_templates/duplicate_redirect/list.html",
        job_callable=duplicate_redirect_worker_entry,
    ),
    "find_and_replace": JobData(
        job_type="find_and_replace",
        job_name="Find and Replace",
        job_list_template="jobs_templates/find_and_replace/list.html",
        job_callable=find_and_replace_worker_entry,
    ),
    "fixred_all": JobData(
        job_type="fixred_all",
        job_name="Fix Redirects in All Pages",
        job_list_template="jobs_templates/fixred_all/list.html",
        job_callable=fixred_all_worker_entry,
    ),
    "fixref": JobData(
        job_type="fixref",
        job_name="Normalize References",
        job_list_template="jobs_templates/fixref/list.html",
        job_callable=fixref_worker_entry,
    ),
    "import_history": JobData(
        job_type="import_history",
        job_name="Import History from Enwiki",
        job_details_template="jobs_templates/import_history/details.html",
        job_list_template="jobs_templates/import_history/list.html",
        job_callable=import_history_worker_entry,
    ),
}

jobs_targets_public = {
    "add_r_column": add_r_column_worker_entry,
    "add_unlinkedwikibase": add_unlinkedwikibase_worker_entry,
    "create_redirects": create_redirects_worker_entry,
    "duplicate_redirect": duplicate_redirect_worker_entry,
    "find_and_replace": find_and_replace_worker_entry,
    "fixred_all": fixred_all_worker_entry,
    "fixref": fixref_worker_entry,
    "import_history": import_history_worker_entry,
}

JOB_TYPE_TEMPLATES_PUBLIC = {
    "add_unlinkedwikibase": "jobs_templates/_help_templates/shared_details.html",
    "fixref": "jobs_templates/_help_templates/shared_details.html",
    "add_r_column": "one_page_templates/add_r_column/details.html",
    "create_redirects": "jobs_templates/create_redirects/details.html",
    "duplicate_redirect": "jobs_templates/duplicate_redirect/details.html",
    "import_history": "jobs_templates/import_history/details.html",
}

JOB_TYPE_LIST_TEMPLATES_PUBLIC = {
    "add_r_column": "one_page_templates/add_r_column/list.html",
    "add_unlinkedwikibase": "jobs_templates/add_unlinkedwikibase/list.html",
    "create_redirects": "jobs_templates/create_redirects/list.html",
    "duplicate_redirect": "jobs_templates/duplicate_redirect/list.html",
    "find_and_replace": "jobs_templates/find_and_replace/list.html",
    "fixred_all": "jobs_templates/fixred_all/list.html",
    "fixref": "jobs_templates/fixref/list.html",
    "import_history": "jobs_templates/import_history/list.html",
}

__all__ = [
    "jobs_data",
    "jobs_targets_public",
    "JOB_TYPE_TEMPLATES_PUBLIC",
]
