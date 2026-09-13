from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.analytics import api as analytics_api
from app.logging_config import setup_logging
from app.redirect import api as redirect_api
from app.write import api as write_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(title="UrlAgent", lifespan=lifespan)

app.include_router(write_api.router)
app.include_router(analytics_api.router)
# Last: GET /{code} is a catch-all for single-segment paths.
app.include_router(redirect_api.router)
