from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Engine, cast, func, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from links_tracking_system.db.session import get_engine
from links_tracking_system.models.url import URL
from links_tracking_system.schemas.url import (
    URLCreate,
    URLListResponse,
    URLResponse,
    URLUpdate,
)

router = APIRouter(prefix="/urls", tags=["urls"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"description": "source_key already exists"}},
)
def create_url(
    payload: URLCreate, engine: Annotated[Engine, Depends(get_engine)]
) -> URLResponse:
    url = URL.model_validate(payload)
    with Session(engine) as session:
        session.add(url)
        try:
            session.commit()
        except IntegrityError:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"URL with source_key {payload.source_key!r} already exists",
            ) from None
        session.refresh(url)
        return URLResponse.model_validate(url, from_attributes=True)


@router.get("")
def list_urls(
    engine: Annotated[Engine, Depends(get_engine)],
    q: Annotated[
        str | None,
        Query(description="Case-insensitive match on source_key, name or tags"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> URLListResponse:
    query = select(URL)
    if q:
        tag_elements = (
            func.jsonb_array_elements_text(
                func.coalesce(URL.tags, cast("[]", JSONB))
            )
            .table_valued("tag")
            .alias("tag_elements")
        )
        matching_tag = (
            select(1)
            .select_from(tag_elements)
            .where(tag_elements.c.tag.icontains(q, autoescape=True))
            .correlate(URL)
            .exists()
        )
        query = query.where(
            or_(
                URL.source_key.icontains(q, autoescape=True),
                URL.name.icontains(q, autoescape=True),
                matching_tag,
            )
        )
    with Session(engine) as session:
        total = session.exec(select(func.count()).select_from(query.subquery())).one()
        rows = session.exec(query.order_by(URL.id).offset(offset).limit(limit)).all()
        return URLListResponse(
            items=[URLResponse.model_validate(r, from_attributes=True) for r in rows],
            total=total,
            limit=limit,
            offset=offset,
        )


@router.get(
    "/{url_id}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "URL not found"}},
)
def read_url(
    url_id: int, engine: Annotated[Engine, Depends(get_engine)]
) -> URLResponse:
    with Session(engine) as session:
        url = session.get(URL, url_id)
        if url is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "URL not found")
        return URLResponse.model_validate(url, from_attributes=True)


@router.patch(
    "/{url_id}",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "URL not found"},
        status.HTTP_409_CONFLICT: {"description": "source_key already exists"},
    },
)
def update_url(
    url_id: int, payload: URLUpdate, engine: Annotated[Engine, Depends(get_engine)]
) -> URLResponse:
    with Session(engine) as session:
        url = session.get(URL, url_id)
        if url is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "URL not found")
        url.sqlmodel_update(payload.model_dump(exclude_unset=True))
        session.add(url)
        try:
            session.commit()
        except IntegrityError:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"URL with source_key {payload.source_key!r} already exists",
            ) from None
        session.refresh(url)
        return URLResponse.model_validate(url, from_attributes=True)


@router.delete(
    "/{url_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": "URL not found"}},
)
def delete_url(url_id: int, engine: Annotated[Engine, Depends(get_engine)]) -> None:
    with Session(engine) as session:
        url = session.get(URL, url_id)
        if url is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "URL not found")
        session.delete(url)
        session.commit()
