from fastapi import APIRouter, HTTPException

from app.models import URLRecord
from app.shared.store import get_store

router = APIRouter()


@router.get("/v1/urls/{code}/stats")
def get_stats(code: str) -> URLRecord:
    record = get_store().get(code)
    if record is None:
        raise HTTPException(status_code=404, detail="unknown code")
    return record
