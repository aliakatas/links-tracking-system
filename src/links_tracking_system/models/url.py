from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class URL(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_key: str = Field(unique=True)
    name: str
    tags: list[str] = Field(default_factory=list, sa_type=JSONB, nullable=True)
