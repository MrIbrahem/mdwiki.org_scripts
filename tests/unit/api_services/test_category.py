from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests
from flask_app.main_app.api_services.category import (
    get_category_members,
)
