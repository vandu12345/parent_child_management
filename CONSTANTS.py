"""
This module contains all Constants
"""

import os

FROM_ADMIN_EMAIL = os.getenv("FROM_ADMIN_EMAIL", "admin@cloudifyapps.com")
HOST_SERVER = (
    f'http://{os.getenv("HOSTED_SERVER", "localhost")}:{os.getenv("PORT", 8000)}'
)

RECEIVER_ADMIN_EMAIL = os.getenv(
    "FROM_ADMIN_EMAIL", "suvendu.mahaptra.official@gmail.com"
)
