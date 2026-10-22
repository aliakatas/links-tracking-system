from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from links_tracking_system.db.session import get_engine
from links_tracking_system.models.url import URL
from links_tracking_system.schemas.url import URLCreate, URLResponse

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
