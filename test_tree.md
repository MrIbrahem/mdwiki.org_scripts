```
tests/
├── integration/
│   ├── app_routes/
│   │   ├── test_dup_route.py
│   │   ├── test_fixred_route.py
│   │   ├── test_fixref_route.py
│   │   ├── test_import_history_route.py
│   │   ├── test_newupdater_route.py
│   │   ├── test_redirect_route.py
│   │   └── test_replace_route.py
│   └── jobs/
│       └── test_jobs_routes.py
├── unit/
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── test_commons_client.py
│   │   │   └── test_wiki_client.py
│   │   ├── test_category.py
│   │   ├── test_mwclient_page.py
│   │   ├── test_pages_api.py
│   │   ├── test_text_api.py
│   │   └── test_text_bot.py
│   ├── app_routes/
│   │   ├── auth/
│   │   │   ├── test_cookie.py
│   │   │   ├── test_oauth.py
│   │   │   ├── test_rate_limit.py
│   │   │   └── test_routes.py
│   │   ├── newupdater/
│   │   │   ├── test_app_routes_worker.py
│   │   │   ├── test_newupdater_worker.py
│   │   │   └── test_route.py
│   │   ├── utils/
│   │   │   └── test_routes_utils.py
│   │   ├── test_fixred.py
│   │   └── test_new_jobs.py
│   ├── config/
│   │   ├── test_classes.py
│   │   ├── test_flask_config.py
│   │   └── test_main_settings.py
│   ├── core/
│   │   ├── test_cookies.py
│   │   └── test_crypto.py
│   ├── db/
│   │   ├── models/
│   │   │   ├── test_jobs.py
│   │   │   └── test_users.py
│   │   ├── services/
│   │   │   ├── test_jobs_service.py
│   │   │   └── test_user_token_service.py
│   │   └── test_exceptions.py
│   ├── jobs/
│   │   └── test_jobs_runner.py
│   ├── new_jobs/
│   │   ├── workers/
│   │   │   ├── create_redirects/
│   │   │   │   └── test_create_redirects_worker.py
│   │   │   ├── duplicate_redirect/
│   │   │   │   └── test_duplicate_redirect_worker.py
│   │   │   ├── find_and_replace/
│   │   │   │   └── test_find_and_replace_worker.py
│   │   │   ├── fixred_all/
│   │   │   │   └── test_fixred_all_worker.py
│   │   │   ├── fixref/
│   │   │   │   └── test_fixref_worker.py
│   │   │   └── import_history/
│   │   │       └── test_import_history_worker.py
│   │   ├── test_base_worker.py
│   │   ├── test_jobs_worker.py
│   │   ├── test_utils.py
│   │   └── test_workers_list.py
│   ├── services/
│   │   ├── fixref/
│   │   │   └── test_fixref_text_new.py
│   │   ├── test_services_fix_duplicate.py
│   │   ├── test_services_fixred.py
│   │   ├── test_services_newupdater.py
│   │   ├── test_services_redirect.py
│   │   └── test_services_replace.py
│   ├── shared/
│   │   ├── fixref_shared/
│   │   │   ├── test_fixred_worker.py
│   │   │   └── test_make_title_bot.py
│   │   ├── new_updater/
│   │   │   ├── bots/
│   │   │   │   ├── test_expend.py
│   │   │   │   ├── test_expend_new.py
│   │   │   │   ├── test_old_params.py
│   │   │   │   └── test_Remove.py
│   │   │   ├── lists/
│   │   │   │   ├── test_bot_params.py
│   │   │   │   ├── test_chem_params.py
│   │   │   │   ├── test_expend_lists.py
│   │   │   │   └── test_identifier_params.py
│   │   │   ├── test_chembox.py
│   │   │   ├── test_drugbox.py
│   │   │   ├── test_helps.py
│   │   │   ├── test_MedWorkNew.py
│   │   │   ├── test_mv_section.py
│   │   │   └── test_resources_new.py
│   │   ├── test_decode_bytes.py
│   │   └── test_fixred_one.py
│   ├── su_services/
│   │   ├── test_jobs_files_service.py
│   │   └── test_users_service.py
│   ├── utils/
│   │   └── test_verify.py
│   └── test_extensions.py
├── __init__.py
└── conftest.py

```