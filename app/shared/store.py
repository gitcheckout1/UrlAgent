import logging
import os

from app.shared.memory_store import MemoryUrlStore
from app.shared.sqlite_store import SqliteUrlStore
from app.shared.store_protocol import UrlStore

logger = logging.getLogger(__name__)

_store: UrlStore | None = None


def _build_store() -> UrlStore:
    """SQLite when DATABASE_URL is set, in-memory otherwise."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.info("store backend=memory")
        return MemoryUrlStore()
    store = SqliteUrlStore(database_url)
    logger.info("store backend=sqlite path=%s", store.path)
    return store


def get_store() -> UrlStore:
    """Resolved on first use, so tests can pin a store before any request."""
    global _store
    if _store is None:
        _store = _build_store()
    return _store


def set_store(store: UrlStore) -> None:
    """Pin the store explicitly. Used by tests to ignore DATABASE_URL."""
    global _store
    _store = store
