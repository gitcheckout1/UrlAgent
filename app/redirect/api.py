import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.shared.memory_store import store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{code}")
def redirect_to_url(code: str) -> RedirectResponse:
    record = store.increment_click(code)
    if record is None:
        logger.info("redirect code=%s status=404", code)
        raise HTTPException(status_code=404, detail="unknown code")

    logger.info("redirect code=%s status=302", code)
    return RedirectResponse(record.url, status_code=302)
