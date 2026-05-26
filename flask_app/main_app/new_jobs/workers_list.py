from .workers.copy_svg_langs.worker import copy_svg_langs_worker_entry
from .workers.create_redirects.worker import create_redirects_worker_entry
from .workers.duplicate_redirect.worker import duplicate_redirect_worker_entry
from .workers.find_and_replace.worker import find_and_replace_worker_entry
from .workers.fixred_all.worker import fixred_all_worker_entry
from .workers.fixref.worker import fixref_worker_entry
from .workers.import_history.worker import import_history_worker_entry

jobs_targets_public = {
    "copy_svg_langs": copy_svg_langs_worker_entry,
    "create_redirects": create_redirects_worker_entry,
    "duplicate_redirect": duplicate_redirect_worker_entry,
    "find_and_replace": find_and_replace_worker_entry,
    "fixred_all": fixred_all_worker_entry,
    "fixref": fixref_worker_entry,
    "import_history": import_history_worker_entry,
}

JOB_TYPE_TEMPLATES_PUBLIC = {
    "copy_svg_langs": "new_jobs_templates/copy_svg_langs/details.html",
    "create_redirects": "new_jobs_templates/create_redirects/details.html",
    "duplicate_redirect": "new_jobs_templates/duplicate_redirect/details.html",
    "find_and_replace": "new_jobs_templates/find_and_replace/details.html",
    "fixred_all": "new_jobs_templates/fixred_all/details.html",
    "fixref": "new_jobs_templates/fixref/details.html",
    "import_history": "new_jobs_templates/import_history/details.html",
}

JOB_TYPE_LIST_TEMPLATES_PUBLIC = {
    "copy_svg_langs": "new_jobs_templates/copy_svg_langs/list.html",
    "create_redirects": "new_jobs_templates/create_redirects/list.html",
    "duplicate_redirect": "new_jobs_templates/duplicate_redirect/list.html",
    "find_and_replace": "new_jobs_templates/find_and_replace/list.html",
    "fixred_all": "new_jobs_templates/fixred_all/list.html",
    "fixref": "new_jobs_templates/fixref/list.html",
    "import_history": "new_jobs_templates/import_history/list.html",
}

__all__ = [
    "jobs_targets_public",
    "JOB_TYPE_TEMPLATES_PUBLIC",
]
