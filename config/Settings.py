import os
from functools import lru_cache
from urllib.parse import quote_plus  # for password is correctly url-encoded


class Settings:
    PG_HOST = os.environ.get("PG_HOST", "localhost")
    PG_USER = os.environ.get("PG_USER", "postgres")
    PG_PASS = os.environ.get("PG_PASS", "admin")
    PG_PORT = os.environ.get("PG_PORT", 5432)
    PG_DB_NAME = os.environ.get("PG_DB_NAME", "parent_child_management")

    DATABASE_URI = f"postgresql+asyncpg://{PG_USER}:{quote_plus(PG_PASS)}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"


# Cache the settings object so that it's not created multiple times
@lru_cache
def get_settings() -> Settings:
    return Settings()
