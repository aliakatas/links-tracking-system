from pydantic import BaseModel, Field


class URLCreate(BaseModel):
    source_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class URLUpdate(BaseModel):
    source_key: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None


class URLResponse(BaseModel):
    id: int
    source_key: str
    name: str
    tags: list[str] | None
