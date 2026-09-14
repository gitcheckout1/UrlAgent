import logging
import time
from collections import deque
from datetime import timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, TypeAdapter, ValidationError

from app.shared.store import get_store

logger = logging.getLogger(__name__)
router = APIRouter()

# HttpUrl accepts http and https only, so this is also the scheme allowlist.
_http_url = TypeAdapter(HttpUrl)

LINK_TTL = timedelta(hours=24)
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW_S = 60.0


class RateLimiter:
    """Sliding window over one process. Not shared across workers."""

    def __init__(self, max_hits: int, window_s: float) -> None:
        self._max_hits = max_hits
        self._window_s = window_s
        self._hits: deque[float] = deque()

    def allow(self) -> bool:
        now = time.monotonic()
        while self._hits and now - self._hits[0] >= self._window_s:
            self._hits.popleft()
        if len(self._hits) >= self._max_hits:
            return False
        self._hits.append(now)
        return True

    def reset(self) -> None:
        self._hits.clear()


ratelimit = RateLimiter(RATE_LIMIT_MAX, RATE_LIMIT_WINDOW_S)


class CreateUrlRequest(BaseModel):
    url: str


class CreateUrlResponse(BaseModel):
    code: str
    url: str


@router.post("/v1/urls", status_code=201)
def create_url(payload: CreateUrlRequest) -> CreateUrlResponse:
    # Counts every attempt, valid or not, since this is abuse protection.
    if not ratelimit.allow():
        logger.info("rate limited path=/v1/urls status=429")
        raise HTTPException(status_code=429, detail="too many requests")

    try:
        url = _http_url.validate_python(payload.url)
    except ValidationError:
        raise HTTPException(status_code=400, detail="url must be an http or https URL")

    record = get_store().create(str(url), ttl=LINK_TTL)
    logger.info("created code=%s", record.code)
    return CreateUrlResponse(code=record.code, url=record.url)
