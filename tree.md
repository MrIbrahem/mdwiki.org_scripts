```
flask_app/
├── main_app/
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── commons_client.py
│   │   │   └── wiki_client.py
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── category.py
│   │   ├── mwclient_page.py
│   │   ├── pages_api.py
│   │   ├── text_api.py
│   │   └── text_bot.py
│   ├── app_routes/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── cookie.py
│   │   │   ├── oauth.py
│   │   │   ├── rate_limit.py
│   │   │   └── routes.py
│   │   ├── main/
│   │   │   └── __init__.py
│   │   ├── newupdater/
│   │   │   ├── __init__.py
│   │   │   ├── route.py
│   │   │   └── worker.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── routes_utils.py
│   │   ├── __init__.py
│   │   ├── fixred.py
│   │   └── new_jobs.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── classes.py
│   │   ├── flask_config.py
│   │   └── main_settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cookies.py
│   │   └── crypto.py
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py
│   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── jobs_service.py
│   │   │   └── user_token_service.py
│   │   ├── __init__.py
│   │   └── exceptions.py
│   ├── new_jobs/
│   │   ├── workers/
│   │   │   ├── copy_svg_langs/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── create_redirects/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── duplicate_redirect/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── find_and_replace/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── fixred_all/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── fixref/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── import_history/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── base_worker.py
│   │   ├── jobs_worker.py
│   │   ├── utils.py
│   │   └── workers_list.py
│   ├── shared/
│   │   ├── fixref_shared/
│   │   │   ├── __init__.py
│   │   │   ├── fixred_worker.py
│   │   │   ├── fixref_text_new.py
│   │   │   └── make_title_bot.py
│   │   ├── new_updater/
│   │   │   ├── bots/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── expend.py
│   │   │   │   ├── expend_new.py
│   │   │   │   ├── old_params.py
│   │   │   │   └── Remove.py
│   │   │   ├── lists/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bot_params.py
│   │   │   │   ├── chem_params.py
│   │   │   │   ├── expend_lists.py
│   │   │   │   └── identifier_params.py
│   │   │   ├── __init__.py
│   │   │   ├── chembox.py
│   │   │   ├── drugbox.py
│   │   │   ├── helps.py
│   │   │   ├── MedWorkNew.py
│   │   │   ├── mv_section.py
│   │   │   └── resources_new.py
│   │   ├── __init__.py
│   │   ├── decode_bytes.py
│   │   └── fixred_one.py
│   ├── su_services/
│   │   ├── __init__.py
│   │   ├── jobs_files_service.py
│   │   └── users_service.py
│   ├── utils/
│   │   └── verify.py
│   ├── __init__.py
│   └── extensions.py
├── static/
├── templates/
│   ├── jobs/
│   ├── jobs_templates/
│   └── new_jobs_templates/
│       ├── copy_svg_langs/
│       ├── create_redirects/
│       ├── duplicate_redirect/
│       ├── find_and_replace/
│       ├── fixred_all/
│       ├── fixref/
│       └── import_history/
├── __init__.py
├── app.py
└── logger_config.py

```