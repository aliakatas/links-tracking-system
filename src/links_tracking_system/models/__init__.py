# Import every model module here so the metadata is fully populated
# when Alembic autogenerates migrations.
from links_tracking_system.db.base import metadata
from links_tracking_system.models.url import URL

__all__ = [
    "URL",
    "metadata",
]
