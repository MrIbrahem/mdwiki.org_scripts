from .admin_service import (
    active_coordinators,
)
from .jobs_service import (
    cancel_job_db,
    create_job,
    delete_job,
    get_job,
    get_user_jobs_stats,
    is_job_cancelled,
    list_jobs,
    update_job_status,
)
from .user_token_service import (
    delete_user_token,
    get_authenticated_user_token,
    get_user_token,
    get_user_token_by_username,
    upsert_user_token,
)
from .users_service import (
    create_user,
    delete_user,
    get_user,
    get_user_by_username,
    list_users,
)

def upsert_user_token_with_username(user_id: int, username: str, access_key: str, access_secret: str) -> None:
    create_user(user_id, username)
    upsert_user_token(
        user_id=user_id,
        access_key=access_key,
        access_secret=access_secret,
    )

__all__ = [
    # users_service
    "get_authenticated_user_token",
    "create_user",
    "get_user",
    "get_user_by_username",
    "delete_user",
    # user_token_service
    "upsert_user_token",
    "get_user_token",
    "delete_user_token",
    "get_user_token_by_username",
    "list_users",
    # jobs_service
    "delete_job",
    "create_job",
    "get_job",
    "list_jobs",
    "update_job_status",
    "get_user_jobs_stats",
    "cancel_job_db",
    "is_job_cancelled",
    "active_coordinators",
]
