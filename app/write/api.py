import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, TypeAdapter, ValidationError

from app.shared.memory_store import store

logger = logging.getLogger(__name__)
router = APIRouter()

# HttpUrl accepts http and https only, so this is also the scheme allowlist.
_http_url = TypeAdapter(HttpUrl)


class CreateUrlRequest(BaseModel):
    url: str


class CreateUrlResponse(BaseModel):
    code: str
    url: str


@router.post("/v1/urls", status_code=201)
def create_url(payload: CreateUrlRequest) -> CreateUrlResponse:
    try:
        url = _http_url.validate_python(payload.url)
    except ValidationError:
        raise HTTPException(status_code=400, detail="url must be an http or https URL")

    record = store.create(str(url))
    logger.info("created code=%s", record.code)
    return CreateUrlResponse(code=record.code, url=record.url)
