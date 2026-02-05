from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.logic import router as logic_router
from .api.songs import router as songs_router
from .db import init_db
from .settings import BASE_DIR


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Guitar Songs", lifespan=lifespan)

app.include_router(songs_router)
app.include_router(logic_router)


static_dir = BASE_DIR / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
