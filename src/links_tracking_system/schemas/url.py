from pydantic import BaseModel, Field


class URLCreate(BaseModel):
    source_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class URLResponse(BaseModel):
    id: int
    source_key: str
    name: str
    tags: list[str] | None
