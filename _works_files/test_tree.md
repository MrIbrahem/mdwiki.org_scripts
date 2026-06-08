```
tests/
├── integration/
│   └── app_routes/
│       ├── admin/
│       │   └── test_admin_routes.py
│       ├── auth/
│       │   └── test_auth_routes.py
│       └── test_jobs_routes.py
├── unit/
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── test_commons_client.py
│   │   │   └── test_wiki_client.py
│   │   ├── test_category.py
│   │   ├── test_mwclient_page.py
│   │   ├── test_pages_api.py
│   │   └── test_query_api.py
│   ├── app_routes/
│   │   ├── admin/
│   │   │   ├── test_admins_required.py
│   │   │   └── test_sidebar.py
│   │   ├── admin_routes/
│   │   │   └── test_coordinators.py
│   │   ├── auth/
│   │   │   ├── test_auth_utils.py
│   │   │   ├── test_cookie.py
│   │   │   ├── test_oauth.py
│   │   │   ├── test_rate_limit.py
│   │   │   └── test_routes.py
│   │   ├── main/
│   │   │   └── test_main_init.py
│   │   ├── newupdater/
│   │   │   ├── test_app_routes_worker.py
│   │   │   ├── test_newupdater_worker.py
│   │   │   └── test_route.py
│   │   ├── utils/
│   │   │   └── test_routes_utils.py
│   │   ├── test_app_routes_init.py
│   │   ├── test_fixred.py
│   │   ├── test_public_jobs.py
│   │   └── test_profile.py
│   ├── config/
│   │   ├── test_classes.py
│   │   ├── test_flask_config.py
│   │   └── test_main_settings.py
│   ├── core/
│   │   ├── test_cookies.py
│   │   ├── test_crypto.py
│   │   └── test_jinja_filters.py
│   ├── db/
│   │   ├── models/
│   │   │   ├── test_jobs.py
│   │   │   └── test_users.py
│   │   ├── services/
│   │   │   ├── test_admin_service.py
│   │   │   ├── test_jobs_service.py
│   │   │   ├── test_services_utils.py
│   │   │   └── test_user_token_service.py
│   │   ├── test_db_init.py
│   │   └── test_exceptions.py
│   ├── public_jobs/
│   │   ├── workers/
│   │   │   ├── add_r_column/
│   │   │   │   ├── test_add_r_column_objects.py
│   │   │   │   ├── test_add_r_column_worker.py
│   │   │   │   └── test_add_rtt.py
│   │   │   ├── add_unlinkedwikibase/
│   │   │   │   └── test_add_unlinkedwikibase_worker.py
│   │   │   ├── create_redirects/
│   │   │   │   ├── test_create_redirects_objects.py
│   │   │   │   └── test_create_redirects_worker.py
│   │   │   ├── duplicate_redirect/
│   │   │   │   └── test_duplicate_redirect_worker.py
│   │   │   ├── find_and_replace/
│   │   │   │   ├── test_find_and_replace_objects.py
│   │   │   │   └── test_find_and_replace_worker.py
│   │   │   ├── fixred_all/
│   │   │   │   └── test_fixred_all_worker.py
│   │   │   ├── fixref/
│   │   │   │   └── test_fixref_worker.py
│   │   │   └── import_history/
│   │   │       ├── test_import_history_objects.py
│   │   │       └── test_import_history_worker.py
│   │   ├── test_base_worker.py
│   │   ├── test_base_worker_object.py
│   │   ├── test_job_lifecycle_updates.py
│   │   ├── test_jobs_worker.py
│   │   ├── test_public_jobs_utils.py
│   │   ├── test_shared_objects.py
│   │   ├── test_utils.py
│   │   └── test_workers_list.py
│   ├── shared/
│   │   ├── fixref_shared/
│   │   │   ├── test_fixred_objects.py
│   │   │   ├── test_fixred_worker.py
│   │   │   ├── test_fixref_text_new.py
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
│   │   ├── replace_wikilink/
│   │   │   └── test_replace_wikilink.py
│   │   ├── test_decode_bytes.py
│   │   ├── test_fixred_one.py
│   │   └── test_shared_classes.py
│   ├── su_services/
│   │   └── test_jobs_files_service.py
│   ├── utils/
│   │   └── test_verify.py
│   ├── test_extensions.py
│   └── test_main_app_init.py
└── conftest.py

```
