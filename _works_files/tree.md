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
│   │   ├── query_api.py
│   │   └── README.md
│   ├── app_routes/
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── admins_required.py
│   │   │   ├── routes.py
│   │   │   └── sidebar.py
│   │   ├── admin_routes/
│   │   │   ├── __init__.py
│   │   │   └── coordinators.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── cookie.py
│   │   │   ├── oauth.py
│   │   │   ├── rate_limit.py
│   │   │   ├── routes.py
│   │   │   └── utils.py
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
│   │   ├── new_jobs.py
│   │   ├── profile.py
│   │   └── README.md
│   ├── config/
│   │   ├── __init__.py
│   │   ├── classes.py
│   │   ├── flask_config.py
│   │   ├── main_settings.py
│   │   └── README.md
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cookies.py
│   │   ├── crypto.py
│   │   ├── jinja_filters.py
│   │   └── README.md
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py
│   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── admin_service.py
│   │   │   ├── jobs_service.py
│   │   │   ├── user_token_service.py
│   │   │   └── utils.py
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   └── README.md
│   ├── new_jobs/
│   │   ├── workers/
│   │   │   ├── add_r_column/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── add_rtt.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   ├── add_unlinkedwikibase/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── create_redirects/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   ├── duplicate_redirect/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── find_and_replace/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   ├── fixred_all/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── fixref/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── import_history/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   ├── __init__.py
│   │   │   └── README.md
│   │   ├── __init__.py
│   │   ├── base_worker_object.py
│   │   ├── jobs_worker.py
│   │   ├── README.md
│   │   ├── shared_objects.py
│   │   ├── utils.py
│   │   └── workers_list.py
│   ├── shared/
│   │   ├── fixref_shared/
│   │   │   ├── __init__.py
│   │   │   ├── fixred_worker.py
│   │   │   ├── fixref_text_new.py
│   │   │   ├── make_title_bot.py
│   │   │   └── objects.py
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
│   │   ├── replace_wikilink/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── decode_bytes.py
│   │   ├── fixred_one.py
│   │   ├── README.md
│   │   └── shared_classes.py
│   ├── su_services/
│   │   ├── __init__.py
│   │   ├── jobs_files_service.py
│   │   ├── README.md
│   │   └── users_service.py
│   ├── utils/
│   │   ├── README.md
│   │   └── verify.py
│   ├── __init__.py
│   ├── extensions.py
│   └── README.md
├── static/
│   ├── css/
│   │   ├── navbar.css
│   │   ├── sidebar-desktop.css
│   │   ├── sidebar-mobile.css
│   │   └── style.css
│   └── js/
│       ├── autocomplete.js
│       ├── card-tools.js
│       ├── dark-mode.js
│       └── sidebar.js
├── templates/
│   ├── admins/
│   ├── jobs_templates/
│   │   ├── _help_templates/
│   │   ├── add_unlinkedwikibase/
│   │   ├── create_redirects/
│   │   ├── duplicate_redirect/
│   │   ├── find_and_replace/
│   │   ├── fixred_all/
│   │   ├── fixref/
│   │   └── import_history/
│   └── one_page_templates/
│       └── add_r_column/
├── __init__.py
├── app.py
├── logger_config.py
├── README.md
└── uwsgi.ini

```