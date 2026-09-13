from datetime import datetime

from pydantic import BaseModel


class URLRecord(BaseModel):
    code: str
    url: str
    clicks: int = 0
    created_at: datetime
    last_clicked_at: datetime | None = None
    # Carried on the model for M6; expiry is not enforced in v1.
    expires_at: datetime | None = None
