from ..objects import JobData
from .add_r_column.worker import add_r_column_worker_entry
from .add_rtt_template.worker import add_rtt_template_worker_entry
from .add_unlinkedwikibase.worker import add_unlinkedwikibase_worker_entry
from .create_redirects.worker import create_redirects_worker_entry
from .duplicate_redirect.worker import duplicate_redirect_worker_entry
from .find_and_replace.worker import find_and_replace_worker_entry
from .fixred_all.worker import fixred_all_worker_entry
from .fixref.worker import fixref_worker_entry
from .import_history.worker import import_history_worker_entry

jobs_data_for_all_pages = {
    "add_unlinkedwikibase": JobData(
        job_type="add_unlinkedwikibase",
        job_name="Add unlinkedwikibase tag",
        job_list_template="jobs_templates/public/add_unlinkedwikibase/list.html",
        job_callable=add_unlinkedwikibase_worker_entry,
        job_args=[],
        start_confirm_message="Start adding unlinkedwikibase tags to all pages?",
    ),
    "fixred_all": JobData(
        job_type="fixred_all",
        job_name="Fix Redirects in All Pages",
        job_list_template="jobs_templates/public/fixred_all/list.html",
        job_callable=fixred_all_worker_entry,
        job_args=[],
        start_confirm_message="Start fixing redirects in all pages?",
        ready=True,
    ),
    "fixref": JobData(
        job_type="fixref",
        job_name="Normalize References",
        job_list_template="jobs_templates/public/fixref/list.html",
        job_callable=fixref_worker_entry,
        job_args=[],
        start_confirm_message="",
    ),
    "duplicate_redirect": JobData(
        job_type="duplicate_redirect",
        job_name="Fix Duplicate Redirects",
        job_details_template="jobs_templates/public/duplicate_redirect/details.html",
        job_list_template="jobs_templates/public/duplicate_redirect/list.html",
        job_callable=duplicate_redirect_worker_entry,
        job_args=[],
        start_confirm_message="Start fixing duplicate redirects?",
        ready=True,
    ),
    "find_and_replace": JobData(
        job_type="find_and_replace",
        job_name="Find and Replace",
        job_list_template="jobs_templates/public/find_and_replace/list.html",
        job_callable=find_and_replace_worker_entry,
        job_args=[],
        start_confirm_message="",
        ready=True,
    ),
    "add_rtt_template": JobData(
        job_type="add_rtt_template",
        job_name="Add RTT Template",
        job_list_template="jobs_templates/public/add_rtt_template/list.html",
        job_callable=add_rtt_template_worker_entry,
        job_args=[],
        start_confirm_message="Start adding RTT template to all Category:RTT pages?",
    ),
}

jobs_data_one_page = {
    "add_r_column": JobData(
        job_type="add_r_column",
        job_name="Add R column",
        job_details_template="one_page_templates/add_r_column/details.html",
        job_list_template="one_page_templates/add_r_column/list.html",
        job_callable=add_r_column_worker_entry,
        job_args=[],
        start_confirm_message="",
        ready=True,
    ),
    "import_history": JobData(
        job_type="import_history",
        job_name="Import History from Enwiki",
        job_details_template="jobs_templates/public/import_history/details.html",
        job_list_template="jobs_templates/public/import_history/list.html",
        job_callable=import_history_worker_entry,
        job_args=[],
        start_confirm_message="",
    ),
    "create_redirects": JobData(
        job_type="create_redirects",
        job_name="Copy Redirects from Enwiki",
        job_details_template="jobs_templates/public/create_redirects/details.html",
        job_list_template="jobs_templates/public/create_redirects/list.html",
        job_callable=create_redirects_worker_entry,
        job_args=[],
        start_confirm_message="",
    ),
}

jobs_data = jobs_data_for_all_pages | jobs_data_one_page

__all__ = [
    "jobs_data_for_all_pages",
    "jobs_data_one_page",
    "jobs_data",
]
