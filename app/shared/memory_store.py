import secrets
import string
from datetime import datetime, timezone

from app.models import URLRecord

CODE_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 7
MAX_CODE_ATTEMPTS = 8


class MemoryUrlStore:
    def __init__(self) -> None:
        self._records: dict[str, URLRecord] = {}

    def _new_code(self) -> str:
        for _ in range(MAX_CODE_ATTEMPTS):
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
            if code not in self._records:
                return code
        raise RuntimeError("could not generate an unused short code")

    def create(self, url: str) -> URLRecord:
        record = URLRecord(
            code=self._new_code(),
            url=url,
            created_at=datetime.now(timezone.utc),
        )
        self._records[record.code] = record
        return record

    def get(self, code: str) -> URLRecord | None:
        return self._records.get(code)

    def increment_click(self, code: str) -> URLRecord | None:
        record = self._records.get(code)
        if record is None:
            return None
        record.clicks += 1
        record.last_clicked_at = datetime.now(timezone.utc)
        return record

    def clear(self) -> None:
        self._records.clear()


store = MemoryUrlStore()
