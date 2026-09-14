from datetime import timedelta
from typing import Protocol

from app.models import URLRecord


class UrlStore(Protocol):
    # ttl None means no expiry; otherwise expires_at is created_at + ttl.
    def create(self, url: str, ttl: timedelta | None = None) -> URLRecord: ...

    def get(self, code: str) -> URLRecord | None: ...

    def increment_click(self, code: str) -> URLRecord | None: ...

    def clear(self) -> None: ...
