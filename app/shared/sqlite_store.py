import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.models import URLRecord

# Share the code-generation policy with the memory store rather than restate it.
from app.shared.memory_store import CODE_ALPHABET, CODE_LENGTH, MAX_CODE_ATTEMPTS

SQLITE_URL_PREFIX = "sqlite:///"

SCHEMA = """
CREATE TABLE IF NOT EXISTS urls (
    code TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    clicks INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    last_clicked_at TEXT,
    expires_at TEXT
)
"""

COLUMNS = "code, url, clicks, created_at, last_clicked_at, expires_at"


def database_path(database_url: str) -> Path:
    if not database_url.startswith(SQLITE_URL_PREFIX):
        raise ValueError(
            f"unsupported DATABASE_URL {database_url!r}; expected {SQLITE_URL_PREFIX}<path>"
        )
    path = database_url[len(SQLITE_URL_PREFIX) :]
    if not path or path == ":memory:":
        raise ValueError("DATABASE_URL must point at a file; :memory: is not supported")
    return Path(path)


def _new_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _parse(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def _to_record(row: tuple) -> URLRecord:
    code, url, clicks, created_at, last_clicked_at, expires_at = row
    return URLRecord(
        code=code,
        url=url,
        clicks=clicks,
        created_at=datetime.fromisoformat(created_at),
        last_clicked_at=_parse(last_clicked_at),
        expires_at=_parse(expires_at),
    )


class SqliteUrlStore:
    """UrlStore backed by stdlib sqlite3. Records returned are snapshots, not live rows."""

    def __init__(self, database_url: str) -> None:
        self.path = database_path(database_url)
        # The store owns its directory, so data/ exists before the first connection.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        # One connection per operation: endpoints run in a threadpool and a
        # sqlite3 connection may not be shared across threads.
        return sqlite3.connect(self.path)

    def create(self, url: str, ttl: timedelta | None = None) -> URLRecord:
        created_at = datetime.now(timezone.utc)
        expires_at = None if ttl is None else created_at + ttl

        with closing(self._connect()) as connection:
            for _ in range(MAX_CODE_ATTEMPTS):
                code = _new_code()
                try:
                    with connection:
                        connection.execute(
                            f"INSERT INTO urls ({COLUMNS}) VALUES (?, ?, 0, ?, NULL, ?)",
                            (code, url, created_at.isoformat(), _iso(expires_at)),
                        )
                except sqlite3.IntegrityError:
                    continue  # code already taken, draw another
                return URLRecord(
                    code=code, url=url, created_at=created_at, expires_at=expires_at
                )
        raise RuntimeError("could not generate an unused short code")

    def get(self, code: str) -> URLRecord | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                f"SELECT {COLUMNS} FROM urls WHERE code = ?", (code,)
            ).fetchone()
        return None if row is None else _to_record(row)

    def increment_click(self, code: str) -> URLRecord | None:
        now = datetime.now(timezone.utc)
        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "UPDATE urls SET clicks = clicks + 1, last_clicked_at = ? WHERE code = ?",
                    (now.isoformat(), code),
                )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                f"SELECT {COLUMNS} FROM urls WHERE code = ?", (code,)
            ).fetchone()
        return None if row is None else _to_record(row)

    def clear(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute("DELETE FROM urls")
