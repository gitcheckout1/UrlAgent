from datetime import datetime, timezone

from pydantic import BaseModel


class URLRecord(BaseModel):
    code: str
    url: str
    clicks: int = 0
    created_at: datetime
    last_clicked_at: datetime | None = None
    # None means the link never expires.
    expires_at: datetime | None = None

    def is_expired(self, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (now or datetime.now(timezone.utc)) >= self.expires_at
