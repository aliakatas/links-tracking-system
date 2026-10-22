from functools import lru_cache

from sqlalchemy import Engine, create_engine

from links_tracking_system.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        # Fail fast instead of hanging requests when Postgres is unreachable.
        connect_args={"connect_timeout": 3},
    )
