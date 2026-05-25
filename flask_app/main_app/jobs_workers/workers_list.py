# from ..public_jobs_workers.copy_svg_langs.worker import copy_svg_langs_worker_entry

copy_svg_langs_worker_entry = None

jobs_targets_public = {
    "copy_svg_langs": copy_svg_langs_worker_entry,
}


JOB_TYPE_TEMPLATES_PUBLIC = {
    "copy_svg_langs": "jobs_templates/copy_svg_langs/details.html",
    "fix_nested_jobs": "jobs_templates/fix_nested_jobs/details.html",
}


JOB_TYPE_LIST_TEMPLATES_PUBLIC = {
    "copy_svg_langs": "jobs_templates/copy_svg_langs/list.html",
    "fix_nested_jobs": "jobs_templates/fix_nested_jobs/list.html",
}


__all__ = [
    "jobs_targets_public",
    "JOB_TYPE_TEMPLATES_PUBLIC",
    "JOB_TYPE_LIST_TEMPLATES_PUBLIC",
]
