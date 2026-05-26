from .workers.copy_svg_langs.worker import copy_svg_langs_worker_entry

jobs_targets_public = {
    "copy_svg_langs": copy_svg_langs_worker_entry,
}

JOB_TYPE_TEMPLATES_PUBLIC = {
    "copy_svg_langs": "new_jobs_templates/copy_svg_langs/details.html",
}

JOB_TYPE_LIST_TEMPLATES_PUBLIC = {
    "copy_svg_langs": "new_jobs_templates/copy_svg_langs/list.html",
}

__all__ = [
    "jobs_targets_public",
    "JOB_TYPE_TEMPLATES_PUBLIC",
]
